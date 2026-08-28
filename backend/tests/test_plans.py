"""Tests for membership plans CRUD (admin) and public listing."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests._helpers import admin_headers, register_customer


def _create_plan(client: TestClient, headers: dict, **overrides) -> dict:
    body = {
        "name": "Monthly",
        "description": "30-day access",
        "duration_days": 30,
        "price_cents": 150000,
        "currency": "PHP",
        "is_active": True,
    }
    body.update(overrides)
    res = client.post("/api/v1/plans/admin", headers=headers, json=body)
    assert res.status_code == 201, res.text
    return res.json()


def test_admin_can_create_and_list_plans(client: TestClient, db_session) -> None:
    h = admin_headers(db_session, "plans-admin@example.com")
    _create_plan(client, h, name="Monthly")
    _create_plan(client, h, name="Annual", duration_days=365, price_cents=1500000)

    res = client.get("/api/v1/plans/admin", headers=h)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    names = {p["name"] for p in data["items"]}
    assert names == {"Monthly", "Annual"}


def test_customer_sees_only_active_plans(client: TestClient, db_session) -> None:
    h = admin_headers(db_session, "plans-admin2@example.com")
    _create_plan(client, h, name="Active Plan", is_active=True)
    _create_plan(client, h, name="Disabled Plan", is_active=False)

    cust = register_customer(client, email="shopper@example.com")
    res = client.get("/api/v1/plans", headers={"Authorization": f"Bearer {cust['access_token']}"})
    assert res.status_code == 200
    items = res.json()["items"]
    assert {p["name"] for p in items} == {"Active Plan"}


def test_admin_can_deactivate_plan(client: TestClient, db_session) -> None:
    h = admin_headers(db_session, "deact-admin@example.com")
    plan = _create_plan(client, h, name="Soon Disabled")

    res = client.delete(f"/api/v1/plans/admin/{plan['id']}", headers=h)
    assert res.status_code == 200
    assert res.json()["is_active"] is False

    res2 = client.get("/api/v1/plans/admin", headers=h)
    assert all(p["is_active"] or p["name"] == "Soon Disabled" for p in res2.json()["items"])


def test_customer_cannot_create_plan(client: TestClient, db_session) -> None:
    cust = register_customer(client, email="not-admin@example.com")
    res = client.post(
        "/api/v1/plans/admin",
        headers={"Authorization": f"Bearer {cust['access_token']}"},
        json={
            "name": "X",
            "duration_days": 30,
            "price_cents": 100,
            "currency": "PHP",
        },
    )
    assert res.status_code == 403


def test_admin_update_plan(client: TestClient, db_session) -> None:
    h = admin_headers(db_session, "upd-admin@example.com")
    plan = _create_plan(client, h, name="Old")

    res = client.patch(
        f"/api/v1/plans/admin/{plan['id']}",
        headers=h,
        json={"name": "New", "price_cents": 99999},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["name"] == "New"
    assert body["price_cents"] == 99999


def test_admin_update_missing_plan_returns_404(client: TestClient, db_session) -> None:
    h = admin_headers(db_session, "missing-admin@example.com")
    res = client.patch("/api/v1/plans/admin/9999", headers=h, json={"name": "Updated"})
    assert res.status_code == 404
