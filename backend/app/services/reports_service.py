"""Aggregations backing the admin reports endpoint (Phase 9).

Bucketing strategy:
  * `bucket_size='day'` — buckets of 1 calendar day
  * `bucket_size='week'` — buckets of 7 calendar days, anchored at the
    start of the requested window.

Period windows:
  * `day` — last 24h, bucketed by hour isn't implemented; we treat
    `period=day` as a special case where `bucket_size` is ignored and a
    single revenue point is returned.
  * `week` — last 7 calendar days, default bucket = day.
  * `month` — last 30 calendar days, default bucket = day.

For SQLite (tests) we rely on `strftime` via SQLAlchemy `func` to keep
queries portable. PostgreSQL could use `date_trunc`.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.membership import Membership, MembershipStatus
from app.models.membership_plan import MembershipPlan
from app.models.payment import Payment, PaymentStatus

Period = Literal["day", "week", "month"]
BucketSize = Literal["day", "week"]

_PERIOD_DAYS: dict[str, int] = {"day": 1, "week": 7, "month": 30}


def _today() -> date:
    return datetime.now(UTC).date()


def _period_bounds(
    period: Period, on: date | None = None
) -> tuple[datetime, datetime]:
    end_date = on or _today()
    start_date = end_date - timedelta(days=_PERIOD_DAYS[period] - 1)
    start = datetime(start_date.year, start_date.month, start_date.day, tzinfo=UTC)
    end_excl = datetime(
        end_date.year, end_date.month, end_date.day, tzinfo=UTC
    ) + timedelta(days=1)
    return start, end_excl


def build_reports(
    db: Session, *, period: Period = "week", bucket_size: BucketSize = "day"
) -> dict:
    today = _today()
    window_start, window_end = _period_bounds(period, today)

    revenue_by_period = _revenue_buckets(
        db, window_start=window_start, window_end=window_end,
        period=period, bucket_size=bucket_size,
    )
    popular_plans = _popular_plans(db, window_start=window_start)
    retention = _retention(db)
    currency = _primary_currency(db)

    return {
        "period": period,
        "bucket_size": "day" if period == "day" else bucket_size,
        "currency": currency,
        "revenue_by_period": revenue_by_period,
        "popular_plans": popular_plans,
        "retention": retention,
    }


def _revenue_buckets(
    db: Session,
    *,
    window_start: datetime,
    window_end: datetime,
    period: Period,
    bucket_size: BucketSize,
) -> list[dict]:
    # For "day" we collapse to one bucket: total today's revenue.
    if period == "day":
        total, count = db.execute(
            select(
                func.coalesce(func.sum(Payment.amount_cents), 0),
                func.count(Payment.id),
            )
            .where(Payment.status == PaymentStatus.SUCCEEDED)
            .where(Payment.paid_at >= window_start)
            .where(Payment.paid_at < window_end)
        ).first()
        return [
            {
                "period_start": window_start.date().isoformat(),
                "revenue_cents": int(total or 0),
                "payments_count": int(count or 0),
            }
        ]

    bucket_days = 1 if bucket_size == "day" else 7

    # Walk bucket-by-bucket so missing days return zeros (matches chart shape).
    out: list[dict] = []
    cursor = datetime(
        window_start.year, window_start.month, window_start.day, tzinfo=UTC
    )
    while cursor < window_end:
        bucket_end = cursor + timedelta(days=bucket_days)
        total, count = db.execute(
            select(
                func.coalesce(func.sum(Payment.amount_cents), 0),
                func.count(Payment.id),
            )
            .where(Payment.status == PaymentStatus.SUCCEEDED)
            .where(Payment.paid_at >= cursor)
            .where(Payment.paid_at < bucket_end)
        ).first()
        out.append(
            {
                "period_start": cursor.date().isoformat(),
                "revenue_cents": int(total or 0),
                "payments_count": int(count or 0),
            }
        )
        cursor = bucket_end
    return out


def _popular_plans(
    db: Session, *, window_start: datetime
) -> list[dict]:
    """Top plans by active members, with lifetime revenue for context."""
    revenue_subq = (
        select(
            Membership.plan_id.label("plan_id"),
            func.coalesce(func.sum(Payment.amount_cents), 0).label("rev"),
        )
        .join(Payment, Payment.membership_id == Membership.id)
        .where(Payment.status == PaymentStatus.SUCCEEDED)
        .where(Payment.paid_at >= window_start)
        .group_by(Membership.plan_id)
        .subquery()
    )

    rows = db.execute(
        select(
            MembershipPlan.id,
            MembershipPlan.name,
            func.count(Membership.id),
            func.coalesce(revenue_subq.c.rev, 0),
        )
        .join(Membership, Membership.plan_id == MembershipPlan.id)
        .outerjoin(
            revenue_subq, revenue_subq.c.plan_id == MembershipPlan.id
        )
        .where(Membership.status == MembershipStatus.ACTIVE)
        .group_by(
            MembershipPlan.id, MembershipPlan.name, revenue_subq.c.rev
        )
        .order_by(func.count(Membership.id).desc())
        .limit(10)
    ).all()
    return [
        {
            "plan_id": pid,
            "plan_name": name,
            "active_members": int(cnt),
            "revenue_cents": int(rev),
        }
        for pid, name, cnt, rev in rows
    ]


def _retention(db: Session) -> dict:
    def n(status: MembershipStatus) -> int:
        return int(
            db.scalar(
                select(func.count(Membership.id)).where(
                    Membership.status == status
                )
            )
            or 0
        )

    active = n(MembershipStatus.ACTIVE)
    cancelled = n(MembershipStatus.CANCELLED)
    expired = n(MembershipStatus.EXPIRED)
    pending = n(MembershipStatus.PENDING)
    total = active + cancelled + expired
    churn = (cancelled / total) if total else 0.0
    return {
        "active": active,
        "cancelled": cancelled,
        "expired": expired,
        "pending": pending,
        "total_lifetime": total,
        "churn_rate": round(churn, 4),
    }


def _primary_currency(db: Session) -> str:
    row = db.execute(
        select(Payment.currency)
        .where(Payment.status == PaymentStatus.SUCCEEDED)
        .group_by(Payment.currency)
        .order_by(func.count(Payment.id).desc())
        .limit(1)
    ).first()
    return row[0] if row else "PHP"
