"""Membership plan — a purchasable offering."""

from __future__ import annotations

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin


class MembershipPlan(Base, TimestampMixin):
    """A membership tier (e.g. Monthly, Quarterly, Annual)."""

    __tablename__ = "membership_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    # Store price as integer cents to avoid float rounding.
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="PHP")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    memberships = relationship("Membership", back_populates="plan")
