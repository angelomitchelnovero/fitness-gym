"""User-related business logic."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.customer_profile import CustomerProfile
from app.models.user import User, UserRole
from app.schemas.auth import RegisterRequest
from app.utils.tokens import new_qr_token


class EmailAlreadyTakenError(Exception):
    """Raised when an email is already registered."""


def create_customer(db: Session, payload: RegisterRequest) -> User:
    """Create a customer account with an empty profile and a fresh QR token."""
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing is not None:
        raise EmailAlreadyTakenError(payload.email)

    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        phone=payload.phone,
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    user.customer_profile = CustomerProfile(qr_token=new_qr_token())

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User | None:
    """Return the user if credentials are valid, else None."""
    user = db.scalar(select(User).where(User.email == email.lower()))
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    user.last_login_at = datetime.now(UTC)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_password(db: Session, user: User, *, current: str, new: str) -> bool:
    """Change a user's password if `current` matches."""
    if not verify_password(current, user.password_hash):
        return False
    user.password_hash = hash_password(new)
    db.add(user)
    db.commit()
    db.refresh(user)
    return True
