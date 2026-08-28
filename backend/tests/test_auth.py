"""Auth flow tests."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _register(
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


def test_register_returns_token_and_creates_user(client: TestClient) -> None:
    body = _register(client)
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["expires_in"] > 0

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    data = me.json()
    assert data["email"] == "alice@example.com"
    assert data["role"] == "customer"
    assert data["is_active"] is True


def test_register_duplicate_email_returns_409(client: TestClient) -> None:
    _register(client, email="dup@example.com")
    res = client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": "password123", "full_name": "Bob"},
    )
    assert res.status_code == 409


def test_register_short_password_rejected(client: TestClient) -> None:
    res = client.post(
        "/api/v1/auth/register",
        json={"email": "weak@example.com", "password": "short", "full_name": "X"},
    )
    assert res.status_code == 422


def test_login_success_and_failure(client: TestClient) -> None:
    _register(client, email="login@example.com", password="password123")
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "password123"},
    )
    assert res.status_code == 200
    assert res.json()["access_token"]

    bad = client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "wrong"},
    )
    assert bad.status_code == 401


def test_me_without_token_returns_401(client: TestClient) -> None:
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401


def test_change_password(client: TestClient) -> None:
    body = _register(client, email="pw@example.com", password="password123")
    headers = {"Authorization": f"Bearer {body['access_token']}"}

    bad = client.post(
        "/api/v1/auth/change-password",
        headers=headers,
        json={"current_password": "wrong", "new_password": "newpassword456"},
    )
    assert bad.status_code == 400

    ok = client.post(
        "/api/v1/auth/change-password",
        headers=headers,
        json={"current_password": "password123", "new_password": "newpassword456"},
    )
    assert ok.status_code == 204

    # New password works.
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "pw@example.com", "password": "newpassword456"},
    )
    assert res.status_code == 200


def test_user_role_guard(client: TestClient) -> None:
    body = _register(client, email="role@example.com", password="password123")
    headers = {"Authorization": f"Bearer {body['access_token']}"}

    res = client.get("/api/v1/users", headers=headers)
    assert res.status_code == 403
