"""Membership business logic — purchase, renew, status transitions."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.membership import Membership, MembershipStatus
from app.models.membership_plan import MembershipPlan
from app.models.user import User


class PlanNotFoundError(Exception):
    pass


class PlanUnavailableError(Exception):
    pass


def _today() -> date:
    return date.today()


def _add_days(start: date, days: int) -> date:
    return start + timedelta(days=days)


def _compute_status(membership: Membership, today: date | None = None) -> MembershipStatus:
    """Return the canonical status for a membership based on dates & stored value."""
    today = today or _today()
    if membership.status == MembershipStatus.CANCELLED:
        return MembershipStatus.CANCELLED
    if membership.status == MembershipStatus.PENDING and membership.activated_at is None:
        return MembershipStatus.PENDING
    if membership.end_date < today:
        return MembershipStatus.EXPIRED
    return MembershipStatus.ACTIVE


def refresh_status(db: Session, membership: Membership) -> Membership:
    """Update membership.status based on current dates; persists if changed."""
    new_status = _compute_status(membership)
    if new_status != membership.status:
        membership.status = new_status
        db.add(membership)
        db.commit()
        db.refresh(membership)
    return membership


def get_user_memberships(db: Session, user: User) -> list[Membership]:
    stmt = (
        select(Membership)
        .where(Membership.user_id == user.id)
        .order_by(Membership.created_at.desc())
    )
    return list(db.scalars(stmt))


def get_active_membership(db: Session, user: User) -> Membership | None:
    today = _today()
    stmt = (
        select(Membership)
        .where(Membership.user_id == user.id)
        .where(Membership.status.in_([MembershipStatus.ACTIVE, MembershipStatus.PENDING]))
        .where(Membership.end_date >= today)
        .order_by(Membership.end_date.desc())
    )
    return db.scalars(stmt).first()


def purchase(db: Session, user: User, plan_id: int) -> Membership:
    """Create a pending membership tied to a plan.

    Phase 4 will activate the membership once payment verifies. Until then, the
    membership stays in `pending` status.
    """
    plan = db.get(MembershipPlan, plan_id)
    if plan is None:
        raise PlanNotFoundError(str(plan_id))
    if not plan.is_active:
        raise PlanUnavailableError("This plan is not currently available.")

    today = _today()
    membership = Membership(
        user_id=user.id,
        plan_id=plan.id,
        start_date=today,
        end_date=_add_days(today, plan.duration_days),
        status=MembershipStatus.PENDING,
        price_cents=plan.price_cents,
        currency=plan.currency,
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


def renew(db: Session, user: User, membership: Membership) -> Membership:
    """Extend (or restart) a membership for another plan duration.

    Renewal creates a new pending membership stacked onto the user. Activation
    happens in Phase 4 alongside the new payment.
    """
    if membership.user_id != user.id:
        raise PermissionError("Membership does not belong to this user.")

    plan = db.get(MembershipPlan, membership.plan_id)
    if plan is None or not plan.is_active:
        raise PlanUnavailableError("The plan attached to this membership is no longer active.")

    base = max(membership.end_date, _today())
    new = Membership(
        user_id=user.id,
        plan_id=plan.id,
        start_date=base,
        end_date=_add_days(base, plan.duration_days),
        status=MembershipStatus.PENDING,
        price_cents=plan.price_cents,
        currency=plan.currency,
    )
    db.add(new)
    db.commit()
    db.refresh(new)
    return new


def cancel(db: Session, user: User, membership: Membership) -> Membership:
    if membership.user_id != user.id:
        raise PermissionError("Membership does not belong to this user.")
    membership.status = MembershipStatus.CANCELLED
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


def list_expiring(db: Session, days: int = 7) -> list[Membership]:
    """Admin helper: memberships expiring within `days` days."""
    today = _today()
    cutoff = today + timedelta(days=days)
    stmt = (
        select(Membership)
        .where(Membership.status == MembershipStatus.ACTIVE)
        .where(Membership.end_date >= today)
        .where(Membership.end_date <= cutoff)
        .order_by(Membership.end_date.asc())
    )
    return list(db.scalars(stmt))


def list_memberships(
    db: Session,
    *,
    status: MembershipStatus | None = None,
    limit: int = 50,
    offset: int = 0,
) -> Iterable[Membership]:
    stmt = select(Membership).order_by(Membership.created_at.desc())
    if status is not None:
        stmt = stmt.where(Membership.status == status)
    return list(db.scalars(stmt.offset(offset).limit(limit)))
