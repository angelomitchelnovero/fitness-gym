"""Membership plan endpoints — public listing and admin CRUD."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.membership_plan import (
    MembershipPlanCreate,
    MembershipPlanListResponse,
    MembershipPlanRead,
    MembershipPlanUpdate,
)
from app.services import plan_service

router = APIRouter()


@router.get(
    "",
    response_model=MembershipPlanListResponse,
    summary="List active membership plans",
)
def list_active_plans(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> MembershipPlanListResponse:
    plans = plan_service.list_plans(db, include_inactive=False)
    return MembershipPlanListResponse(
        items=[MembershipPlanRead.model_validate(p) for p in plans],
        total=len(plans),
    )


# -------- Admin --------


@router.get(
    "/admin",
    response_model=MembershipPlanListResponse,
    summary="List ALL plans (admin)",
    dependencies=[Depends(require_admin)],
)
def admin_list_plans(
    include_inactive: bool = Query(default=True),
    db: Session = Depends(get_db),
) -> MembershipPlanListResponse:
    plans = plan_service.list_plans(db, include_inactive=include_inactive)
    return MembershipPlanListResponse(
        items=[MembershipPlanRead.model_validate(p) for p in plans],
        total=len(plans),
    )


@router.post(
    "/admin",
    response_model=MembershipPlanRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a plan",
    dependencies=[Depends(require_admin)],
)
def admin_create_plan(
    payload: MembershipPlanCreate, db: Session = Depends(get_db)
) -> MembershipPlanRead:
    plan = plan_service.create_plan(db, payload)
    return MembershipPlanRead.model_validate(plan)


@router.patch(
    "/admin/{plan_id}",
    response_model=MembershipPlanRead,
    summary="Update a plan",
    dependencies=[Depends(require_admin)],
)
def admin_update_plan(
    plan_id: int,
    payload: MembershipPlanUpdate,
    db: Session = Depends(get_db),
) -> MembershipPlanRead:
    try:
        plan = plan_service.get_plan(db, plan_id)
    except plan_service.PlanNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Plan not found") from exc
    plan = plan_service.update_plan(db, plan, payload)
    return MembershipPlanRead.model_validate(plan)


@router.delete(
    "/admin/{plan_id}",
    response_model=MembershipPlanRead,
    summary="Deactivate a plan",
    dependencies=[Depends(require_admin)],
)
def admin_deactivate_plan(
    plan_id: int, db: Session = Depends(get_db)
) -> MembershipPlanRead:
    try:
        plan = plan_service.get_plan(db, plan_id)
    except plan_service.PlanNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Plan not found") from exc
    plan = plan_service.deactivate_plan(db, plan)
    return MembershipPlanRead.model_validate(plan)
