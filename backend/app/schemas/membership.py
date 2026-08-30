"""Schemas for memberships."""

from __future__ import annotations

from datetime import date, datetime
from pydantic import BaseModel, ConfigDict

from app.models.membership import MembershipStatus
from app.schemas.membership_plan import MembershipPlanRead
from app.schemas.user import UserSummary


class MembershipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    plan_id: int
    start_date: date
    end_date: date
    status: MembershipStatus
    price_cents: int
    currency: str
    activated_at: datetime | None
    created_at: datetime


class MembershipWithPlan(MembershipRead):
    plan: MembershipPlanRead


class MembershipWithUserAndPlan(MembershipRead):
    user: UserSummary
    plan: MembershipPlanRead


class PurchaseMembershipRequest(BaseModel):
    plan_id: int


class MembershipListResponse(BaseModel):
    items: list[MembershipWithPlan | MembershipWithUserAndPlan]
    total: int
