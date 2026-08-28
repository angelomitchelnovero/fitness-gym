"""Tests for the customer dashboard summary endpoint."""

from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient

from tests._helpers import admin_headers, register_customer


def _create_plan(
    client: TestClient, headers: dict, **overrides
) -> dict:
    body = {
        "name": "Dash Cust Monthly",
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


def test_dashboard_requires_auth(client: TestClient, db_session) -> None:
    res = client.get("/api/v1/dashboard/me")
    assert res.status_code == 401


def test_dashboard_returns_baseline_shape(
    client: TestClient, db_session
) -> None:
    cust = register_customer(client, email="cust-dash-baseline@example.com")
    cust_h = {"Authorization": f"Bearer {cust['access_token']}"}
    res = client.get("/api/v1/dashboard/me", headers=cust_h)
    assert res.status_code == 200, res.text
    body = res.json()
    for key in (
        "user",
        "active_membership",
        "pending_membership",
        "days_remaining",
        "expiring_soon",
        "expiring_today",
        "spend_30d_cents",
        "spend_total_cents",
        "currency",
        "recent_payments",
        "recent_checkins",
    ):
        assert key in body, f"missing: {key}"
    assert body["user"]["email"] == "cust-dash-baseline@example.com"
    assert body["active_membership"] is None


def test_dashboard_reflects_active_membership_and_spend(
    client: TestClient, db_session
) -> None:
    h = admin_headers(db_session, "cust-dash-admin@example.com")
    plan = _create_plan(client, h)
    cust = register_customer(client, email="cust-dash-active@example.com")
    cust_h = {"Authorization": f"Bearer {cust['access_token']}"}
    membership = _purchase_and_activate(client, h, cust_h, plan["id"])

    res = client.get("/api/v1/dashboard/me", headers=cust_h)
    body = res.json()
    assert body["active_membership"] is not None
    assert body["active_membership"]["id"] == membership["id"]
    assert body["active_membership"]["status"] == "active"
    # 30-day window.
    assert body["spend_30d_cents"] >= plan["price_cents"]
    assert body["spend_total_cents"] >= plan["price_cents"]
    assert any(
        p["id"] is not None for p in body["recent_payments"]
    )


def test_dashboard_expiring_soon_flag(
    client: TestClient, db_session
) -> None:
    h = admin_headers(db_session, "cust-dash-exp-admin@example.com")
    plan = _create_plan(client, h)
    cust = register_customer(client, email="cust-dash-expiring@example.com")
    cust_h = {"Authorization": f"Bearer {cust['access_token']}"}
    membership = _purchase_and_activate(client, h, cust_h, plan["id"])

    # Manually move the membership end_date forward 5 days so it counts as
    # expiring-soon (≤7 days from today).
    from sqlalchemy.orm import Session as SessionT

    # Use a synthetic session to update the row.
    db: SessionT = db_session  # alias for clarity
    from app.models.membership import Membership as MModel

    m = db.get(MModel, membership["id"])
    assert m is not None
    m.end_date = date.today() + timedelta(days=5)
    db.commit()

    res = client.get("/api/v1/dashboard/me", headers=cust_h)
    body = res.json()
    assert body["expiring_soon"] is True
    assert body["expiring_today"] is False
    assert 0 < (body["days_remaining"] or 0) <= 7


def test_dashboard_recent_checkins(
    client: TestClient, db_session
) -> None:
    h = admin_headers(db_session, "cust-dash-ci-admin@example.com")
    plan = _create_plan(client, h)
    cust = register_customer(client, email="cust-dash-ci@example.com")
    cust_h = {"Authorization": f"Bearer {cust['access_token']}"}
    _purchase_and_activate(client, h, cust_h, plan["id"])

    # Check in via the card.
    card = client.get("/api/v1/checkin/card", headers=cust_h).json()
    client.post("/api/v1/checkin/scan", headers=h, json={"token": card["token"]})

    res = client.get("/api/v1/dashboard/me", headers=cust_h)
    body = res.json()
    assert body["recent_checkins"][0]["accepted"] is True