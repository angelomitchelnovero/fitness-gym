"""Customer and admin membership endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import require_admin, require_customer
from app.db.session import get_db
from app.models.membership import Membership
from app.models.user import User
from app.schemas.membership import (
    MembershipListResponse,
    MembershipWithPlan,
    MembershipWithUserAndPlan,
    PurchaseMembershipRequest,
)
from app.services import membership_service

router = APIRouter()


def _serialize_admin(m: Membership) -> MembershipWithUserAndPlan:
    return MembershipWithUserAndPlan.model_validate(m)

def _serialize(m: Membership) -> MembershipWithPlan:
    return MembershipWithPlan.model_validate(m)


@router.get(
    "/me",
    response_model=MembershipListResponse,
    summary="List my memberships",
)
def my_memberships(
    db: Session = Depends(get_db),
    user: User = Depends(require_customer),
) -> MembershipListResponse:
    items = membership_service.get_user_memberships(db, user)
    return MembershipListResponse(
        items=[_serialize(m) for m in items],
        total=len(items),
    )


@router.post(
    "",
    response_model=MembershipWithPlan,
    status_code=status.HTTP_201_CREATED,
    summary="Purchase a membership",
)
def purchase(
    payload: PurchaseMembershipRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_customer),
) -> MembershipWithPlan:
    try:
        membership = membership_service.purchase(db, user, payload.plan_id)
    except membership_service.PlanNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Plan not found") from exc
    except membership_service.PlanUnavailableError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _serialize(membership)


@router.post(
    "/{membership_id}/renew",
    response_model=MembershipWithPlan,
    summary="Renew a membership",
)
def renew(
    membership_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_customer),
) -> MembershipWithPlan:
    membership = db.get(Membership, membership_id)
    if membership is None or membership.user_id != user.id:
        raise HTTPException(status_code=404, detail="Membership not found")
    try:
        new_membership = membership_service.renew(db, user, membership)
    except membership_service.PlanUnavailableError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _serialize(new_membership)


@router.post(
    "/{membership_id}/cancel",
    response_model=MembershipWithPlan,
    summary="Cancel a membership",
)
def cancel(
    membership_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_customer),
) -> MembershipWithPlan:
    membership = db.get(Membership, membership_id)
    if membership is None or membership.user_id != user.id:
        raise HTTPException(status_code=404, detail="Membership not found")
    membership = membership_service.cancel(db, user, membership)
    return _serialize(membership)


# -------- Admin --------


@router.get(
    "/admin/list",
    response_model=MembershipListResponse,
    summary="List memberships (admin)",
    dependencies=[Depends(require_admin)],
)
def admin_list(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> MembershipListResponse:
    # Need total count of all memberships for pagination
    from sqlalchemy import func
    from app.models.membership import Membership
    total = db.scalar(select(func.count(Membership.id))) or 0

    items = membership_service.list_memberships(db, limit=limit, offset=offset)
    return MembershipListResponse(
        items=[_serialize_admin(m) for m in items],
        total=total,
    )


@router.get(
    "/admin/expiring",
    response_model=MembershipListResponse,
    summary="Memberships expiring soon (admin)",
    dependencies=[Depends(require_admin)],
)
def admin_expiring(
    days: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db),
) -> MembershipListResponse:
    items = membership_service.list_expiring(db, days=days)
    return MembershipListResponse(
        items=[_serialize_admin(m) for m in items],
        total=len(items),
    )
