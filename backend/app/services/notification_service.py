"""Notification orchestration: enqueue + deliver.

Most callers want `enqueue_and_send` — it creates a `Notification` row in
PENDING state, attempts delivery through the configured channel, and
updates the row to SENT (with `sent_at`) or FAILED (with `error`).
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.membership import Membership, MembershipStatus
from app.models.notification import (
    Notification,
    NotificationKind,
    NotificationStatus,
)
from app.models.payment import Payment, PaymentStatus
from app.models.user import User
from app.services.notifications.base import NotificationMessage
from app.services.notifications.registry import get_channel


def _send_via_channel(notification: Notification) -> None:
    """Try to deliver. Updates `notification.status` in place."""
    channel = get_channel(notification.channel)
    result = channel.send(
        NotificationMessage(
            recipient=notification.recipient,
            subject=notification.subject,
            body=notification.body,
            kind=notification.kind,
        )
    )
    if result.ok:
        notification.status = NotificationStatus.SENT
        notification.sent_at = datetime.now(UTC)
        notification.error = None
    else:
        notification.status = NotificationStatus.FAILED
        notification.error = result.error


def enqueue_and_send(
    db: Session,
    *,
    user: User,
    kind: str,
    subject: str,
    body: str,
    related_payment_id: int | None = None,
    related_membership_id: int | None = None,
    related_check_in_id: int | None = None,
    channel: str | None = None,
) -> Notification:
    """Create a row + attempt delivery in the same transaction."""
    notif = Notification(
        user_id=user.id,
        channel=channel or settings.NOTIFICATION_CHANNEL,
        kind=kind,
        subject=subject,
        body=body,
        recipient=user.email,
        related_payment_id=related_payment_id,
        related_membership_id=related_membership_id,
        related_check_in_id=related_check_in_id,
    )
    db.add(notif)
    db.flush()  # populate notif.id before delivery
    _send_via_channel(notif)
    db.commit()
    db.refresh(notif)
    return notif


def list_for_user(db: Session, user: User, *, limit: int = 50) -> list[Notification]:
    return list(
        db.scalars(
            select(Notification)
            .where(Notification.user_id == user.id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
    )


# --- Triggers ---

def trigger_payment_receipt(
    db: Session, payment: Payment, user: User
) -> Notification | None:
    if payment.status != PaymentStatus.SUCCEEDED:
        return None
    return enqueue_and_send(
        db,
        user=user,
        kind=NotificationKind.PAYMENT_RECEIPT,
        subject="Payment received",
        body=(
            f"Hi {user.full_name},\n\n"
            f"We received your payment of {payment.amount_cents/100:.2f} "
            f"{payment.currency}. Your membership is now active.\n\n"
            "Thanks for training with us!\n"
        ),
        related_payment_id=payment.id,
    )


def trigger_checkin_confirmation(
    db: Session, *, user: User, check_in_id: int
) -> Notification:
    return enqueue_and_send(
        db,
        user=user,
        kind=NotificationKind.CHECKIN_CONFIRMATION,
        subject="Check-in confirmed",
        body=(
            f"Hi {user.full_name},\n\n"
            "Thanks for visiting FitnessGym today. See you again soon!\n"
        ),
        related_check_in_id=check_in_id,
    )


def trigger_membership_expiring(
    db: Session, *, user: User, membership: Membership, days_left: int
) -> Notification:
    return enqueue_and_send(
        db,
        user=user,
        kind=NotificationKind.MEMBERSHIP_EXPIRING,
        subject="Your membership is expiring soon",
        body=(
            f"Hi {user.full_name},\n\n"
            f"Your membership ends in {days_left} day(s). "
            "Renew now to keep your access uninterrupted.\n"
        ),
        related_membership_id=membership.id,
    )


def send_expiry_reminders(db: Session, *, days: int | None = None) -> int:
    """Find memberships expiring within `days` and enqueue a reminder each.

    Returns the count of reminders sent.
    """
    from datetime import timedelta

    window = days if days is not None else settings.MEMBERSHIP_EXPIRY_REMINDER_DAYS
    if hasattr(window, "days"):
        window = window.days
    today = datetime.now(UTC).date()
    cutoff = today + timedelta(days=int(window))
    stmt = (
        select(Membership, User)
        .join(User, User.id == Membership.user_id)
        .where(Membership.status == MembershipStatus.ACTIVE)
        .where(Membership.end_date >= today)
        .where(Membership.end_date <= cutoff)
    )
    sent = 0
    for membership, user in db.execute(stmt).all():
        days_left = (membership.end_date - today).days
        trigger_membership_expiring(
            db, user=user, membership=membership, days_left=days_left
        )
        sent += 1
    return sent