"""Check-in endpoints: card issuance, scan, history."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models.membership import Membership, MembershipStatus
from app.models.user import User
from app.schemas.checkin import (
    CardResponse,
    CheckInListResponse,
    CheckInRead,
    ScanOutcome,
    ScanRequest,
)
from app.services import checkin_service, qr_service

router = APIRouter()


def _active_membership(db: Session, user: User) -> Membership | None:
    """Return the user's current active membership, if any."""
    from sqlalchemy import select

    stmt = (
        select(Membership)
        .where(Membership.user_id == user.id)
        .where(Membership.status == MembershipStatus.ACTIVE)
        .order_by(Membership.end_date.desc())
    )
    return db.scalars(stmt).first()


@router.get(
    "/card",
    response_model=CardResponse,
    summary="Issue a short-lived QR membership card for the current user",
)
def issue_card(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CardResponse:
    membership = _active_membership(db, user)
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active membership — purchase a plan to get a QR card",
        )
    card = qr_service.issue_card(user, membership)
    return CardResponse(
        token=card.token,
        membership_id=membership.id,
        user_id=user.id,
        plan_name=membership.plan.name if membership.plan else "Unknown Plan",
        issued_at=card.issued_at,
        expires_at=card.expires_at,
    )


@router.post(
    "/scan",
    response_model=ScanOutcome,
    summary="[staff] Process a scanned QR token",
)
def scan(
    body: ScanRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_admin),
) -> ScanOutcome:
    try:
        record = checkin_service.scan(
            db, token=body.token, actor=actor, source=body.source,
        )
    except checkin_service.CardInvalidError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except checkin_service.CardReplayError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except checkin_service.MemberInadmissibleError as exc:
        # Already persisted as a denied CheckIn; surface reason to the staff.
        raise HTTPException(
            status_code=403,
            detail=exc.reason or "Member not admissible",
        ) from exc
    return ScanOutcome(
        accepted=True,
        reason=None,
        user_id=record.user_id,
        membership_id=record.membership_id,
        scanned_at=record.scanned_at,
        check_in_id=record.id,
    )


@router.get(
    "/me",
    response_model=CheckInListResponse,
    summary="List my recent check-ins",
)
def my_checkins(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CheckInListResponse:
    items = checkin_service.list_for_user(db, user)
    return CheckInListResponse(
        items=[CheckInRead.model_validate(c) for c in items],
        total=len(items),
    )


admin_router = APIRouter()


@admin_router.get(
    "",
    response_model=CheckInListResponse,
    summary="[admin] List check-ins for a given day (defaults to today)",
)
def list_all(
    on_date: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> CheckInListResponse:
    items = checkin_service.list_all(db, on_date=on_date)
    return CheckInListResponse(
        items=[CheckInRead.model_validate(c) for c in items],
        total=len(items),
    )