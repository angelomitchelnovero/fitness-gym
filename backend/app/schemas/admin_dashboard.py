"""Schemas for the admin dashboard summary."""

from __future__ import annotations

from pydantic import BaseModel


class PlanBreakdownEntry(BaseModel):
    plan_id: int
    plan_name: str
    active_count: int


class RecentPaymentEntry(BaseModel):
    id: int
    user_id: int
    membership_id: int | None
    amount_cents: int
    currency: str
    status: str
    paid_at: str | None
    created_at: str


class RecentMembershipEntry(BaseModel):
    id: int
    user_id: int
    plan_id: int
    plan_name: str | None
    status: str
    start_date: str
    end_date: str


class DashboardSummary(BaseModel):
    """Top-level admin dashboard response."""

    # Membership totals
    active_memberships: int
    pending_memberships: int
    expiring_within_days: int       # active & end_date within window
    expired_last_30_days: int
    cancelled_memberships: int

    # Today's check-ins
    today_checkins_total: int
    today_checkins_accepted: int
    today_checkins_rejected: int

    # Revenue (succeeded payments, all-time for now)
    total_revenue_cents: int
    currency: str

    # Drill-down lists
    plan_breakdown: list[PlanBreakdownEntry]
    recent_payments: list[RecentPaymentEntry]
    recent_memberships: list[RecentMembershipEntry]