"""Schemas for the admin reports endpoint (Phase 9)."""

from __future__ import annotations

from pydantic import BaseModel


class RevenuePoint(BaseModel):
    period_start: str  # ISO date — first day of the bucket
    revenue_cents: int
    payments_count: int


class PlanPopularity(BaseModel):
    plan_id: int
    plan_name: str
    active_members: int
    revenue_cents: int


class RetentionSummary(BaseModel):
    active: int
    cancelled: int
    expired: int
    pending: int
    total_lifetime: int
    churn_rate: float  # cancelled / total_lifetime, 0..1


class ReportsResponse(BaseModel):
    """The full reports payload for the requested window."""

    period: str            # day | week | month (the requested range)
    bucket_size: str       # day | week (granularity)
    currency: str
    revenue_by_period: list[RevenuePoint]
    popular_plans: list[PlanPopularity]
    retention: RetentionSummary
