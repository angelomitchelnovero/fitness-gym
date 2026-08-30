"""Schemas for the customer dashboard."""

from __future__ import annotations

from pydantic import BaseModel


class DashboardUser(BaseModel):
    id: int
    full_name: str
    email: str


class MembershipSummary(BaseModel):
    id: int
    plan_id: int
    plan_name: str
    status: str
    start_date: str | None
    end_date: str | None
    price_cents: int
    currency: str
    activated_at: str | None


class RecentPaymentEntry(BaseModel):
    id: int
    amount_cents: int
    currency: str
    status: str
    paid_at: str | None
    created_at: str


class RecentCheckInEntry(BaseModel):
    id: int
    scanned_at: str
    accepted: bool
    reason: str | None


class CustomerDashboard(BaseModel):
    user: DashboardUser
    active_membership: MembershipSummary | None
    pending_membership: MembershipSummary | None
    days_remaining: int | None
    expiring_soon: bool
    expiring_today: bool
    spend_30d_cents: int
    spend_total_cents: int
    currency: str
    recent_payments: list[RecentPaymentEntry]
    recent_checkins: list[RecentCheckInEntry]