"""Seed the lone admin account.

Usage:
    python -m app.scripts.seed_admin --email admin@fitnessgym.local --password secret123

Idempotent: re-running with the same email is a no-op.
"""

from __future__ import annotations

import argparse
import sys

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import session_scope
from app.models.gym_settings import GymSettings
from app.models.user import User, UserRole


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed the admin account")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--full-name", default="Gym Admin")
    args = parser.parse_args()

    with session_scope() as db:
        existing = db.scalar(select(User).where(User.email == args.email.lower()))
        if existing is not None:
            print(f"Admin {args.email} already exists; skipping.")
            return 0

        admin = User(
            email=args.email.lower(),
            password_hash=hash_password(args.password),
            full_name=args.full_name,
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin)

        # Ensure singleton settings row exists.
        settings_row = db.get(GymSettings, 1)
        if settings_row is None:
            db.add(GymSettings(id=1))

        db.flush()
        print(f"Created admin {admin.email} (id={admin.id}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
