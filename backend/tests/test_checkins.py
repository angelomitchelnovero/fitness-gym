"""Tests for membership card issuance, QR scanning, and history."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests._helpers import admin_headers, register_customer


def _create_plan(
    client: TestClient, headers: dict, **overrides
) -> dict:
    body = {
        "name": "Checkin Monthly",
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
    """Buy a membership and force-verify a payment so it becomes ACTIVE."""
    res = client.post(
        "/api/v1/memberships", headers=cust_h, json={"plan_id": plan_id}
    )
    assert res.status_code == 201, res.text
    membership = res.json()
    res = client.post(
        "/api/v1/payments/checkout",
        headers=cust_h,
        json={"membership_id": membership["id"], "provider": "mock"},
    )
    assert res.status_code == 201
    payment_id = res.json()["payment"]["id"]
    res = client.post(
        f"/api/v1/payments/{payment_id}/verify",
        headers=cust_h,
        json={"force_outcome": "succeeded"},
    )
    assert res.status_code == 200
    res = client.get("/api/v1/memberships/me", headers=cust_h)
    me = next(m for m in res.json()["items"] if m["id"] == membership["id"])
    assert me["status"] == "active"
    return me


def test_issue_card_returns_token(client: TestClient, db_session) -> None:
    h = admin_headers(db_session, "card-admin@example.com")
    plan = _create_plan(client, h)
    cust = register_customer(client, email="card-cust@example.com")
    cust_h = {"Authorization": f"Bearer {cust['access_token']}"}
    _purchase_and_activate(client, h, cust_h, plan["id"])

    res = client.get("/api/v1/checkin/card", headers=cust_h)
    assert res.status_code == 200
    body = res.json()
    assert body["token"].count(".") == 2  # JWT shape
    assert body["membership_id"] > 0
    assert body["issued_at"] <= body["expires_at"]


def test_issue_card_requires_active_membership(
    client: TestClient, db_session
) -> None:
    cust = register_customer(client, email="no-mem@example.com")
    cust_h = {"Authorization": f"Bearer {cust['access_token']}"}
    res = client.get("/api/v1/checkin/card", headers=cust_h)
    assert res.status_code == 404


def test_scan_happy_path_admits(client: TestClient, db_session) -> None:
    h = admin_headers(db_session, "scan-admin@example.com")
    plan = _create_plan(client, h)
    cust = register_customer(client, email="scan-cust@example.com")
    cust_h = {"Authorization": f"Bearer {cust['access_token']}"}
    _purchase_and_activate(client, h, cust_h, plan["id"])

    card = client.get("/api/v1/checkin/card", headers=cust_h).json()
    res = client.post(
        "/api/v1/checkin/scan",
        headers=h,
        json={"token": card["token"], "source": "qr"},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["accepted"] is True
    assert body["membership_id"] == card["membership_id"]


def test_scan_rejects_replay(client: TestClient, db_session) -> None:
    h = admin_headers(db_session, "replay-admin@example.com")
    plan = _create_plan(client, h)
    cust = register_customer(client, email="replay-cust@example.com")
    cust_h = {"Authorization": f"Bearer {cust['access_token']}"}
    _purchase_and_activate(client, h, cust_h, plan["id"])

    card = client.get("/api/v1/checkin/card", headers=cust_h).json()
    first = client.post(
        "/api/v1/checkin/scan", headers=h, json={"token": card["token"]}
    )
    assert first.status_code == 200

    # Same token, second scan → 409.
    second = client.post(
        "/api/v1/checkin/scan", headers=h, json={"token": card["token"]}
    )
    assert second.status_code == 409


def test_scan_rejects_expired_token(client: TestClient, db_session) -> None:
    """A tampered/expired token must be rejected with 400."""
    register_customer(client, email="expired-cust@example.com")
    res = client.post(
        "/api/v1/checkin/scan",
        headers=admin_headers(db_session, "expired-admin@example.com"),
        json={"token": "not-a-real-token"},
    )
    assert res.status_code == 400


def test_customer_cannot_scan(client: TestClient, db_session) -> None:
    cust = register_customer(client, email="no-scan@example.com")
    cust_h = {"Authorization": f"Bearer {cust['access_token']}"}
    res = client.post(
        "/api/v1/checkin/scan", headers=cust_h, json={"token": "anything"}
    )
    assert res.status_code == 403


def test_me_lists_checkins(client: TestClient, db_session) -> None:
    h = admin_headers(db_session, "listme-admin@example.com")
    plan = _create_plan(client, h)
    cust = register_customer(client, email="listme-cust@example.com")
    cust_h = {"Authorization": f"Bearer {cust['access_token']}"}
    _purchase_and_activate(client, h, cust_h, plan["id"])
    card = client.get("/api/v1/checkin/card", headers=cust_h).json()
    client.post("/api/v1/checkin/scan", headers=h, json={"token": card["token"]})

    res = client.get("/api/v1/checkin/me", headers=cust_h)
    assert res.status_code == 200
    body = res.json()
    assert body["total"] >= 1
    assert body["items"][0]["accepted"] is True


def test_admin_lists_checkins_for_day(client: TestClient, db_session) -> None:
    h = admin_headers(db_session, "listday-admin@example.com")
    plan = _create_plan(client, h)
    cust = register_customer(client, email="listday-cust@example.com")
    cust_h = {"Authorization": f"Bearer {cust['access_token']}"}
    _purchase_and_activate(client, h, cust_h, plan["id"])
    card = client.get("/api/v1/checkin/card", headers=cust_h).json()
    client.post("/api/v1/checkin/scan", headers=h, json={"token": card["token"]})

    res = client.get("/api/v1/admin/checkins", headers=h)
    assert res.status_code == 200
    assert res.json()["total"] >= 1