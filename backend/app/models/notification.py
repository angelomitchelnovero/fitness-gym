"""Notification rows — one per outbound message we want to deliver."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin


class NotificationStatus:
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class NotificationKind:
    PAYMENT_RECEIPT = "payment_receipt"
    MEMBERSHIP_EXPIRING = "membership_expiring"
    CHECKIN_CONFIRMATION = "checkin_confirmation"


class Notification(Base, TimestampMixin):
    """An outbound notification — email today, SMS/push later.

    The actual send happens via a `NotificationChannel` provider; this table
    captures the intent and the outcome so we can show the user an inbox
    and audit what was sent.
    """

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    channel: Mapped[str] = mapped_column(String(20), nullable=False, default="email")
    kind: Mapped[str] = mapped_column(String(60), nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    recipient: Mapped[str] = mapped_column(String(200), nullable=False)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=NotificationStatus.PENDING
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Optional links back to source records (denormalized for traceability).
    related_payment_id: Mapped[int | None] = mapped_column(
        ForeignKey("payments.id", ondelete="SET NULL"), nullable=True
    )
    related_membership_id: Mapped[int | None] = mapped_column(
        ForeignKey("memberships.id", ondelete="SET NULL"), nullable=True
    )
    related_check_in_id: Mapped[int | None] = mapped_column(
        ForeignKey("check_ins.id", ondelete="SET NULL"), nullable=True
    )