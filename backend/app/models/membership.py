"""Customer membership — ties a user to a plan over a date range."""

from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin


class MembershipStatus(str, enum.Enum):  # noqa: UP042 - keep (str, Enum) for Alembic
    """Lifecycle states for a membership."""

    PENDING = "pending"       # created, awaiting payment (Phase 4)
    ACTIVE = "active"         # paid, within date range
    EXPIRED = "expired"       # past end_date
    CANCELLED = "cancelled"   # manually cancelled

    def __str__(self) -> str:  # noqa: D401 - StrEnum compatibility shim
        return self.value


class Membership(Base, TimestampMixin):
    """A user's enrollment in a specific plan."""

    __tablename__ = "memberships"
    __table_args__ = (
        Index("ix_memberships_user_status", "user_id", "status"),
        Index("ix_memberships_end_date", "end_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("membership_plans.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[MembershipStatus] = mapped_column(
        Enum(
            MembershipStatus,
            name="membership_status",
            native_enum=False,
            length=20,
        ),
        nullable=False,
        default=MembershipStatus.PENDING,
    )

    # Snapshot of the price at purchase time (cents).
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="PHP")

    # Set when payment is verified (Phase 4).
    activated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    payment_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "payments.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_memberships_payment_id",
        ),
        nullable=True,
        unique=True,
    )

    payments = relationship(
        "Payment",
        primaryjoin="Membership.id == Payment.membership_id",
        foreign_keys="Payment.membership_id",
        viewonly=True,
    )

    user = relationship("User", back_populates="memberships")
    plan = relationship("MembershipPlan", back_populates="memberships")
    payment = relationship("Payment", foreign_keys=[payment_id], post_update=True)
