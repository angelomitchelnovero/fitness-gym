"""Tests for the admin dashboard summary endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests._helpers import admin_headers, register_customer


def _create_plan(
    client: TestClient, headers: dict, **overrides
) -> dict:
    body = {
        "name": "Dash Monthly",
        "description": "30 days",
        "duration_days": 30,
        "price_cents": 99000,
        "currency": "PHP",
        "is_active": True,
    }
    body.update(overrides)
    res = client.post("/api/v1/plans/admin", headers=headers, json=body)
    assert res.status_code == 201, res.text
    return res.json()


def _purchase_and_activate(
    client: TestClient, admin_h: dict, cust_h: dict, plan_id: int
) -> dict:
    res = client.post("/api/v1/memberships", headers=cust_h, json={"plan_id": plan_id})
    assert res.status_code == 201, res.text
    membership = res.json()
    res = client.post(
        "/api/v1/payments/checkout",
        headers=cust_h,
        json={"membership_id": membership["id"], "provider": "mock"},
    )
    payment_id = res.json()["payment"]["id"]
    res = client.post(
        f"/api/v1/payments/{payment_id}/verify",
        headers=cust_h,
        json={"force_outcome": "succeeded"},
    )
    assert res.status_code == 200
    return membership


def test_dashboard_requires_admin(client: TestClient, db_session) -> None:
    cust = register_customer(client, email="dash-cust@example.com")
    cust_h = {"Authorization": f"Bearer {cust['access_token']}"}
    res = client.get("/api/v1/admin/dashboard", headers=cust_h)
    assert res.status_code == 403


def test_dashboard_returns_baseline_shape(
    client: TestClient, db_session
) -> None:
    h = admin_headers(db_session, "dash-base-admin@example.com")
    res = client.get("/api/v1/admin/dashboard", headers=h)
    assert res.status_code == 200, res.text
    body = res.json()
    for key in (
        "active_memberships",
        "pending_memberships",
        "expiring_within_days",
        "expired_last_30_days",
        "cancelled_memberships",
        "today_checkins_total",
        "today_checkins_accepted",
        "today_checkins_rejected",
        "total_revenue_cents",
        "currency",
        "plan_breakdown",
        "recent_payments",
        "recent_memberships",
    ):
        assert key in body, f"missing key: {key}"


def test_dashboard_counts_reflect_data(
    client: TestClient, db_session
) -> None:
    """Insert a plan, an active membership, and a check-in; totals must move."""
    h = admin_headers(db_session, "dash-data-admin@example.com")
    plan = _create_plan(client, h)
    cust = register_customer(client, email="dash-active@example.com")
    cust_h = {"Authorization": f"Bearer {cust['access_token']}"}
    membership = _purchase_and_activate(client, h, cust_h, plan["id"])

    # Issue a card and check the customer in.
    card = client.get("/api/v1/checkin/card", headers=cust_h).json()
    res = client.post("/api/v1/checkin/scan", headers=h, json={"token": card["token"]})
    assert res.status_code == 200

    res = client.get("/api/v1/admin/dashboard", headers=h)
    body = res.json()
    assert body["active_memberships"] >= 1
    assert body["today_checkins_total"] >= 1
    assert body["today_checkins_accepted"] >= 1
    assert body["total_revenue_cents"] >= plan["price_cents"]
    assert any(p["plan_id"] == plan["id"] for p in body["plan_breakdown"])
    assert any(m["id"] == membership["id"] for m in body["recent_memberships"])
    assert any(p["membership_id"] == membership["id"] for p in body["recent_payments"])