"""Aggregate model imports so Alembic can discover metadata."""

from app.db.base import Base  # noqa: F401
from app.models.customer_profile import CustomerProfile  # noqa: F401
from app.models.gym_settings import GymSettings  # noqa: F401
from app.models.user import User  # noqa: F401
