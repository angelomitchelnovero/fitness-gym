"""Shared test helpers."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.user import User, UserRole


def register_customer(
    client: TestClient,
    email: str = "alice@example.com",
    password: str = "password123",
) -> dict:
    res = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Alice Example",
            "phone": "+639170000000",
        },
    )
    assert res.status_code == 201, res.text
    return res.json()


def make_admin(db: Session, email: str = "admin@example.com") -> User:
    admin = User(
        email=email,
        password_hash=hash_password("adminpass123"),
        full_name="Test Admin",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def admin_token(admin: User) -> str:
    return create_access_token(
        admin.id, extra={"role": admin.role.value, "email": admin.email}
    )


def admin_headers(db: Session, email: str = "admin@example.com") -> dict[str, str]:
    admin = make_admin(db, email=email)
    return {"Authorization": f"Bearer {admin_token(admin)}"}


def customer_headers(register_response: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {register_response['access_token']}"}
