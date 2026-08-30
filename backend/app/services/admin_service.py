"""Read-only aggregates for the admin dashboard."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.check_in import CheckIn
from app.models.membership import Membership, MembershipStatus
from app.models.membership_plan import MembershipPlan
from app.models.payment import Payment, PaymentStatus
from app.models.user import User


def _today() -> date:
    return datetime.now(UTC).date()


def _day_bounds(d: date | None = None) -> tuple[datetime, datetime]:
    d = d or _today()
    start = datetime(d.year, d.month, d.day, tzinfo=UTC)
    end = start + timedelta(days=1)
    return start, end


def build_dashboard(db: Session) -> dict[str, Any]:
    today = _today()

    # --- Membership totals ---
    active_count = db.scalar(
        select(func.count(Membership.id))
        .where(Membership.status == MembershipStatus.ACTIVE)
    ) or 0
    pending_count = db.scalar(
        select(func.count(Membership.id))
        .where(Membership.status == MembershipStatus.PENDING)
    ) or 0
    cancelled_count = db.scalar(
        select(func.count(Membership.id))
        .where(Membership.status == MembershipStatus.CANCELLED)
    ) or 0
    expiring_count = db.scalar(
        select(func.count(Membership.id))
        .where(Membership.status == MembershipStatus.ACTIVE)
        .where(Membership.end_date >= today)
        .where(Membership.end_date <= today + timedelta(days=7))
    ) or 0
    expired_recent = db.scalar(
        select(func.count(Membership.id))
        .where(Membership.status == MembershipStatus.EXPIRED)
        .where(Membership.end_date >= today - timedelta(days=30))
    ) or 0

    # --- Today's check-ins ---
    day_start, day_end = _day_bounds(today)
    today_total = db.scalar(
        select(func.count(CheckIn.id))
        .where(CheckIn.scanned_at >= day_start)
        .where(CheckIn.scanned_at < day_end)
    ) or 0
    today_accepted = db.scalar(
        select(func.count(CheckIn.id))
        .where(CheckIn.scanned_at >= day_start)
        .where(CheckIn.scanned_at < day_end)
        .where(CheckIn.accepted.is_(True))
    ) or 0

    # --- Revenue: succeeded payments ---
    rev_row = db.execute(
        select(func.coalesce(func.sum(Payment.amount_cents), 0))
        .where(Payment.status == PaymentStatus.SUCCEEDED)
    ).first()
    total_revenue_cents = int(rev_row[0]) if rev_row else 0
    currency = (
        db.scalar(
            select(Payment.currency)
            .where(Payment.status == PaymentStatus.SUCCEEDED)
            .order_by(Payment.created_at.desc())
            .limit(1)
        )
        or "PHP"
    )

    # --- Plan breakdown (active members per plan) ---
    breakdown_rows = db.execute(
        select(
            MembershipPlan.id,
            MembershipPlan.name,
            func.count(Membership.id),
        )
        .join(Membership, Membership.plan_id == MembershipPlan.id)
        .where(Membership.status == MembershipStatus.ACTIVE)
        .group_by(MembershipPlan.id, MembershipPlan.name)
        .order_by(func.count(Membership.id).desc())
    ).all()
    plan_breakdown = [
        {"plan_id": pid, "plan_name": pname, "active_count": cnt}
        for pid, pname, cnt in breakdown_rows
    ]

    # --- Recent payments (last 5) ---
    recent_payments_rows = db.execute(
        select(Payment, User.full_name)
        .join(User, Payment.user_id == User.id)
        .order_by(Payment.created_at.desc())
        .limit(5)
    ).all()
    recent_payments = [
        {
            "id": row.Payment.id,
            "user_id": row.Payment.user_id,
            "user_name": row.full_name,
            "membership_id": row.Payment.membership_id,
            "amount_cents": row.Payment.amount_cents,
            "currency": row.Payment.currency,
            "status": row.Payment.status,
            "paid_at": row.Payment.paid_at.isoformat() if row.Payment.paid_at else None,
            "created_at": row.Payment.created_at.isoformat(),
        }
        for row in recent_payments_rows
    ]

    # --- Recent memberships (last 5) ---
    recent_memberships_rows = db.execute(
        select(Membership, MembershipPlan.name, User.full_name)
        .join(MembershipPlan, MembershipPlan.id == Membership.plan_id)
        .join(User, Membership.user_id == User.id)
        .order_by(Membership.created_at.desc())
        .limit(5)
    ).all()
    recent_memberships = [
        {
            "id": row.Membership.id,
            "user_id": row.Membership.user_id,
            "user_name": row.full_name,
            "plan_id": row.Membership.plan_id,
            "plan_name": row.name,
            "status": row.Membership.status.value if hasattr(row.Membership.status, "value") else str(row.Membership.status),
            "start_date": row.Membership.start_date.isoformat(),
            "end_date": row.Membership.end_date.isoformat(),
        }
        for row in recent_memberships_rows
    ]

    return {
        "active_memberships": int(active_count),
        "pending_memberships": int(pending_count),
        "expiring_within_days": int(expiring_count),
        "expired_last_30_days": int(expired_recent),
        "cancelled_memberships": int(cancelled_count),
        "today_checkins_total": int(today_total),
        "today_checkins_accepted": int(today_accepted),
        "today_checkins_rejected": int(today_total) - int(today_accepted),
        "total_revenue_cents": int(total_revenue_cents),
        "currency": currency,
        "plan_breakdown": plan_breakdown,
        "recent_payments": recent_payments,
        "recent_memberships": recent_memberships,
    }