"""QR membership-card issuance and verification.

The QR is a short-lived HS256 JWT carrying the user's id, membership id,
and a unique jti. The token is *untrusted* — any tampering (or use after
expiry) is rejected by signature/expiry checks here, and any reuse within
the TTL is rejected by `QrTokenUse` (anti-replay).
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings
from app.models.membership import Membership, MembershipStatus
from app.models.user import User

CARD_TOKEN_TYPE = "card"  # noqa: S105 — not a credential, just a JWT typ tag


@dataclass(frozen=True)
class IssuedCard:
    token: str
    jti: str
    issued_at: datetime
    expires_at: datetime


def issue_card(user: User, membership: Membership, *, ttl_seconds: int = 300) -> IssuedCard:
    """Sign a short-lived JWT for the user's active membership."""
    now = datetime.now(UTC)
    jti = secrets.token_urlsafe(16)
    payload: dict[str, Any] = {
        "sub": str(user.id),
        "mid": membership.id,
        "jti": jti,
        "typ": CARD_TOKEN_TYPE,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl_seconds)).timestamp()),
        "role": "card",
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    expires_at = now + timedelta(seconds=ttl_seconds)
    return IssuedCard(token=token, jti=jti, issued_at=now, expires_at=expires_at)


def verify_card_token(token: str) -> dict[str, Any]:
    """Decode + validate. Raises `JWTError` on bad signature/expiry/format.

    Caller is responsible for anti-replay and membership-validity checks.
    """
    payload = jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
    )
    if payload.get("typ") != CARD_TOKEN_TYPE:
        raise JWTError("Token type is not a membership card")
    if not payload.get("jti"):
        raise JWTError("Token missing jti")
    if not payload.get("mid"):
        raise JWTError("Token missing mid")
    return payload


def membership_is_admittable(
    membership: Membership,
    today: datetime | None = None,
) -> tuple[bool, str | None]:
    """Returns (ok, reason_if_not). Cancelled/expired/pending memberships can't enter."""
    today = today or datetime.now(UTC)
    if membership.status == MembershipStatus.CANCELLED:
        return False, "Membership cancelled"
    if membership.status == MembershipStatus.PENDING:
        return False, "Membership not yet paid"
    if membership.activated_at is None:
        return False, "Membership not activated"
    # Compare calendar dates, not full datetimes.
    if membership.end_date and membership.end_date < today.date():
        return False, "Membership expired"
    return True, None