"""Placeholder Payment model — full logic lands in Phase 4.

We need a real table now because `Membership.payment_id` has a FK to it. The
Phase 4 work will fill in provider, status, verification logic, etc.
"""

from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="PHP")
    provider: Mapped[str] = mapped_column(String(40), nullable=False, default="mock")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    reference: Mapped[str | None] = mapped_column(String(120), nullable=True)

    # Backref to memberships is added in Phase 4 when the payment schema
    # knows about memberships. For now we keep this table as a pure placeholder
    # so the FK column on Membership has a target.
