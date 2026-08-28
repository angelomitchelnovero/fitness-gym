#!/usr/bin/env python
"""Seed (or rotate) a single admin user.

Usage:
  ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD=secret .venv/bin/python scripts/seed_admin.py
  .venv/bin/python scripts/seed_admin.py --rotate
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Make `app` importable when running from the repo root.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import select  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rotate", action="store_true",
                        help="Reset the password of an existing admin.")
    args = parser.parse_args()

    email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    password = os.getenv("ADMIN_PASSWORD")
    if not password:
        print("ADMIN_PASSWORD env var is required", file=sys.stderr)
        return 2

    with SessionLocal() as db:
        existing = db.scalar(select(User).where(User.email == email))
        if existing is None:
            u = User(
                email=email,
                password_hash=hash_password(password),
                full_name="Administrator",
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(u)
            db.commit()
            print(f"created admin {u.email} (id={u.id})")
            return 0

        if not args.rotate:
            print(f"admin {email} already exists (use --rotate to reset).")
            return 0

        existing.password_hash = hash_password(password)
        existing.role = UserRole.ADMIN
        existing.is_active = True
        db.commit()
        print(f"rotated password for {email}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
