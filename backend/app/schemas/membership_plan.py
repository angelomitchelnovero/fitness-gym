"""Schemas for membership plans."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MembershipPlanBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    duration_days: int = Field(ge=1, le=3650)
    price_cents: int = Field(ge=0)
    currency: str = Field(default="PHP", min_length=2, max_length=8)
    is_active: bool = True


class MembershipPlanCreate(MembershipPlanBase):
    pass


class MembershipPlanUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    duration_days: int | None = Field(default=None, ge=1, le=3650)
    price_cents: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=2, max_length=8)
    is_active: bool | None = None


class MembershipPlanRead(MembershipPlanBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class MembershipPlanListResponse(BaseModel):
    items: list[MembershipPlanRead]
    total: int
