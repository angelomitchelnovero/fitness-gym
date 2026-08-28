"""Payment record — one row per transaction attempt."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin


class PaymentStatus:
    """String constants for payment.status.

    Stored as a plain `String` column (not Enum) to make provider-side
    transitions easier to evolve without Alembic enum migrations.
    """

    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # One membership per payment (set when a payment is tied to a purchase/renewal).
    membership_id: Mapped[int | None] = mapped_column(
        ForeignKey("memberships.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="PHP")

    provider: Mapped[str] = mapped_column(String(40), nullable=False, default="mock")
    external_id: Mapped[str | None] = mapped_column(String(120), nullable=True, unique=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=PaymentStatus.PENDING, index=True
    )
    method: Mapped[str | None] = mapped_column(String(40), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    membership = relationship(
        "Membership",
        foreign_keys=[membership_id],
        back_populates="payments",
    )