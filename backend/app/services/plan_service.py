"""Plan management business logic."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.membership_plan import MembershipPlan
from app.schemas.membership_plan import MembershipPlanCreate, MembershipPlanUpdate


class PlanNotFoundError(Exception):
    pass


def list_plans(db: Session, *, include_inactive: bool = False) -> list[MembershipPlan]:
    stmt = select(MembershipPlan).order_by(MembershipPlan.price_cents.asc())
    if not include_inactive:
        stmt = stmt.where(MembershipPlan.is_active.is_(True))
    return list(db.scalars(stmt))


def get_plan(db: Session, plan_id: int) -> MembershipPlan:
    plan = db.get(MembershipPlan, plan_id)
    if plan is None:
        raise PlanNotFoundError(str(plan_id))
    return plan


def create_plan(db: Session, payload: MembershipPlanCreate) -> MembershipPlan:
    plan = MembershipPlan(**payload.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def update_plan(
    db: Session, plan: MembershipPlan, payload: MembershipPlanUpdate
) -> MembershipPlan:
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(plan, field, value)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def deactivate_plan(db: Session, plan: MembershipPlan) -> MembershipPlan:
    plan.is_active = False
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan
