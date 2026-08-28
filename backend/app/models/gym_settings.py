"""Gym-wide settings (singleton row)."""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin


class GymSettings(Base, TimestampMixin):
    __tablename__ = "gym_settings"

    # Single-row table; id is fixed to 1.
    id: Mapped[int] = mapped_column(primary_key=True, default=1)

    gym_name: Mapped[str] = mapped_column(String(120), nullable=False, default="FitnessGym")
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="PHP")
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="Asia/Manila")
