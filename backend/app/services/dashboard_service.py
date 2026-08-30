"""Read-only aggregates for the customer's own dashboard."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.check_in import CheckIn
from app.models.membership import Membership, MembershipStatus
from app.models.payment import Payment, PaymentStatus
from app.models.user import User


def _today() -> date:
    return datetime.now(UTC).date()


def build_customer_dashboard(db: Session, user: User) -> dict[str, Any]:
    today = _today()
    month_start = datetime(today.year, today.month, 1, tzinfo=UTC)

    # --- Memberships ---
    memberships = list(
        db.scalars(
            select(Membership)
            .where(Membership.user_id == user.id)
            .order_by(Membership.created_at.desc())
        )
    )
    active = next(
        (m for m in memberships if m.status == MembershipStatus.ACTIVE),
        None,
    )
    pending = next(
        (m for m in memberships if m.status == MembershipStatus.PENDING),
        None,
    )

    days_remaining: int | None = None
    expiring_soon = False
    expiring_today = False
    if active is not None and active.end_date is not None:
        days_remaining = (active.end_date - today).days
        expiring_soon = 0 < days_remaining <= 7
        expiring_today = days_remaining == 0

    # --- Payments ---
    spend_30d_row = db.execute(
        select(func.coalesce(func.sum(Payment.amount_cents), 0))
        .where(Payment.user_id == user.id)
        .where(Payment.status == PaymentStatus.SUCCEEDED)
        .where(Payment.paid_at is not None)
        .where(Payment.paid_at >= month_start)
    ).first()
    spend_30d = int(spend_30d_row[0]) if spend_30d_row else 0

    spend_total_row = db.execute(
        select(func.coalesce(func.sum(Payment.amount_cents), 0))
        .where(Payment.user_id == user.id)
        .where(Payment.status == PaymentStatus.SUCCEEDED)
    ).first()
    spend_total = int(spend_total_row[0]) if spend_total_row else 0

    currency = (
        db.scalar(
            select(Payment.currency)
            .where(Payment.user_id == user.id)
            .where(Payment.status == PaymentStatus.SUCCEEDED)
            .order_by(Payment.created_at.desc())
            .limit(1)
        )
        or "PHP"
    )

    last_payments = list(
        db.scalars(
            select(Payment)
            .where(Payment.user_id == user.id)
            .order_by(Payment.created_at.desc())
            .limit(5)
        )
    )
    recent_payments = [
        {
            "id": p.id,
            "amount_cents": p.amount_cents,
            "currency": p.currency,
            "status": p.status,
            "paid_at": p.paid_at.isoformat() if p.paid_at else None,
            "created_at": p.created_at.isoformat(),
        }
        for p in last_payments
    ]

    # --- Check-ins (last 5) ---
    last_checkins = list(
        db.scalars(
            select(CheckIn)
            .where(CheckIn.user_id == user.id)
            .order_by(CheckIn.scanned_at.desc())
            .limit(5)
        )
    )
    recent_checkins = [
        {
            "id": c.id,
            "scanned_at": c.scanned_at.isoformat(),
            "accepted": bool(c.accepted),
            "reason": c.reason,
        }
        for c in last_checkins
    ]

    def _serialize_membership(m: Membership) -> dict[str, Any]:
        return {
            "id": m.id,
            "plan_id": m.plan_id,
            "plan_name": m.plan.name if m.plan else "Unknown Plan",
            "status": m.status.value if hasattr(m.status, "value") else str(m.status),
            "start_date": m.start_date.isoformat() if m.start_date else None,
            "end_date": m.end_date.isoformat() if m.end_date else None,
            "price_cents": m.price_cents,
            "currency": m.currency,
            "activated_at": m.activated_at.isoformat() if m.activated_at else None,
        }

    return {
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
        },
        "active_membership": _serialize_membership(active) if active else None,
        "pending_membership": _serialize_membership(pending) if pending else None,
        "days_remaining": days_remaining,
        "expiring_soon": expiring_soon,
        "expiring_today": expiring_today,
        "spend_30d_cents": spend_30d,
        "spend_total_cents": spend_total,
        "currency": currency,
        "recent_payments": recent_payments,
        "recent_checkins": recent_checkins,
    }