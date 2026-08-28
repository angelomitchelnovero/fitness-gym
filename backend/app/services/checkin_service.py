"""Check-in orchestration: validate QR tokens, anti-replay, record events."""

from __future__ import annotations

from datetime import UTC, datetime

from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.check_in import CheckIn, QrTokenUse
from app.models.membership import Membership
from app.models.user import User
from app.services import qr_service


class CardInvalidError(Exception):
    """Signature, expiry, or token-shape failure."""


class CardReplayError(Exception):
    """Same jti already used within the TTL window."""


class MemberInadmissibleError(Exception):
    """Membership itself is expired/cancelled/pending."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def scan(
    db: Session,
    *,
    token: str,
    actor: User,
    source: str = "qr",
) -> CheckIn:
    """Process a scanned QR token.

    Returns the persisted `CheckIn` row. If the person is inadmissible, the
    row is still recorded (with `accepted=False`) so staff have an audit
    trail — except for replays, which we silently refuse without persisting
    the duplicate attempt.
    """
    now = datetime.now(UTC)

    # 1. Signature / shape / expiry.
    try:
        payload = qr_service.verify_card_token(token)
    except JWTError as exc:
        raise CardInvalidError(str(exc)) from exc

    jti = payload["jti"]
    mid = int(payload["mid"])
    sub = int(payload["sub"])

    # 2. Anti-replay — refuse before even looking up the membership.
    used = db.scalar(select(QrTokenUse).where(QrTokenUse.jti == jti))
    if used is not None:
        raise CardReplayError(
            f"QR token already used at {used.used_at.isoformat()}"
        )

    # 3. Resolve the membership/user pair.
    membership = db.get(Membership, mid)
    user = db.get(User, sub)
    if membership is None or user is None or membership.user_id != user.id:
        raise CardInvalidError("Token references unknown membership/user pair")

    # 4. Decide admission.
    ok, reason = qr_service.membership_is_admittable(membership, today=now)

    record = CheckIn(
        user_id=user.id,
        membership_id=membership.id,
        scanned_at=now,
        source=source,
        accepted=ok,
        reason=None if ok else reason,
        actor_user_id=actor.id,
    )
    if ok:
        # Persist the jti BEFORE commit so a duplicate scan that races against
        # this one will see the row in its own transaction.
        db.add(QrTokenUse(
            jti=jti,
            user_id=user.id,
            membership_id=membership.id,
            used_at=now,
        ))
    db.add(record)
    db.commit()
    db.refresh(record)

    if not ok:
        raise MemberInadmissibleError(reason or "not admissible")
    return record


def list_for_user(db: Session, user: User, *, limit: int = 50) -> list[CheckIn]:
    stmt = (
        select(CheckIn)
        .where(CheckIn.user_id == user.id)
        .order_by(CheckIn.scanned_at.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt))


def list_all(
    db: Session,
    *,
    on_date: datetime | None = None,
    limit: int = 200,
) -> list[CheckIn]:
    on_date = on_date or datetime.now(UTC)
    day_start = on_date.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start.replace(hour=23, minute=59, second=59, microsecond=999_000)
    stmt = (
        select(CheckIn)
        .where(CheckIn.scanned_at >= day_start)
        .where(CheckIn.scanned_at <= day_end)
        .order_by(CheckIn.scanned_at.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt))