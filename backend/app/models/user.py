"""User model — covers admin and customer accounts."""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin


class UserRole(str, enum.Enum):  # noqa: UP042 - keep (str, Enum) for Alembic enum compatibility
    """Single role enum. Admin is the only staff role."""

    ADMIN = "admin"
    CUSTOMER = "customer"

    def __str__(self) -> str:  # noqa: D401 - StrEnum compatibility shim
        return self.value


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=False, length=20),
        nullable=False,
        default=UserRole.CUSTOMER,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    customer_profile = relationship(
        "CustomerProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    memberships = relationship("Membership", back_populates="user")
