"""Check-in records — one row each time a customer is admitted at the desk."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin


class CheckIn(Base, TimestampMixin):
    """A single check-in event. `accepted=False` records a denied scan too."""

    __tablename__ = "check_ins"
    __table_args__ = (
        Index("ix_check_ins_user_time", "user_id", "scanned_at"),
        Index("ix_check_ins_scanned_at", "scanned_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    membership_id: Mapped[int | None] = mapped_column(
        ForeignKey("memberships.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    source: Mapped[str] = mapped_column(
        String(20), nullable=False, default="qr"
    )  # "qr" | "manual"
    accepted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Optional reference to the staff/admin who performed the scan.
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    user = relationship("User", foreign_keys=[user_id])
    membership = relationship("Membership", foreign_keys=[membership_id])


class QrTokenUse(Base):
    """Records one consumption of a QR token (anti-replay).

    Storing `(jti, used_at)` lets us reject a second scan of the same QR
    within the token's TTL.
    """

    __tablename__ = "qr_token_uses"
    __table_args__ = (Index("ix_qr_token_uses_used_at", "used_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    jti: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    membership_id: Mapped[int | None] = mapped_column(
        ForeignKey("memberships.id", ondelete="SET NULL"), nullable=True
    )
    used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )