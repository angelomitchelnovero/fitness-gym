"""Tests for the payment flow."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests._helpers import admin_headers, register_customer


def _create_plan(
    client: TestClient, headers: dict, **overrides
) -> dict:
    body = {
        "name": "Pay Monthly",
        "description": "30 days",
        "duration_days": 30,
        "price_cents": 150000,
        "currency": "PHP",
        "is_active": True,
    }
    body.update(overrides)
    res = client.post("/api/v1/plans/admin", headers=headers, json=body)
    assert res.status_code == 201, res.text
    return res.json()


def _purchase_pending(client: TestClient, headers: dict, plan_id: int) -> dict:
    res = client.post(
        "/api/v1/memberships", headers=headers, json={"plan_id": plan_id}
    )
    assert res.status_code == 201, res.text
    return res.json()


def test_checkout_creates_pending_payment(
    client: TestClient, db_session
) -> None:
    h = admin_headers(db_session, "checkout-admin@example.com")
    plan = _create_plan(client, h)
    cust = register_customer(client, email="payer@example.com")
    cust_headers = {"Authorization": f"Bearer {cust['access_token']}"}
    membership = _purchase_pending(client, cust_headers, plan["id"])

    res = client.post(
        "/api/v1/payments/checkout",
        headers=cust_headers,
        json={"membership_id": membership["id"], "provider": "mock"},
    )
    assert res.status_code == 201, res.text
    body = res.json()
    payment = body["payment"]
    assert payment["status"] == "pending"
    assert payment["membership_id"] == membership["id"]
    assert payment["provider"] == "mock"
    assert payment["external_id"].startswith("pi_mock_")
    assert payment["amount_cents"] == plan["price_cents"]
    assert payment["currency"] == "PHP"


def test_checkout_rejects_other_users_membership(
    client: TestClient, db_session
) -> None:
    h = admin_headers(db_session, "reject-admin@example.com")
    plan = _create_plan(client, h)

    alice = register_customer(client, email="alice-owner@example.com")
    bob = register_customer(client, email="bob-snooper@example.com")
    bob_headers = {"Authorization": f"Bearer {bob['access_token']}"}

    alice_membership = _purchase_pending(
        client, {"Authorization": f"Bearer {alice['access_token']}"}, plan["id"]
    )

    res = client.post(
        "/api/v1/payments/checkout",
        headers=bob_headers,
        json={"membership_id": alice_membership["id"], "provider": "mock"},
    )
    assert res.status_code == 403


def test_verify_success_activates_membership(
    client: TestClient, db_session
) -> None:
    h = admin_headers(db_session, "verify-admin@example.com")
    plan = _create_plan(client, h)
    cust = register_customer(client, email="verifier@example.com")
    cust_headers = {"Authorization": f"Bearer {cust['access_token']}"}
    membership = _purchase_pending(client, cust_headers, plan["id"])

    checkout = client.post(
        "/api/v1/payments/checkout",
        headers=cust_headers,
        json={"membership_id": membership["id"], "provider": "mock"},
    ).json()
    payment_id = checkout["payment"]["id"]

    res = client.post(
        f"/api/v1/payments/{payment_id}/verify",
        headers=cust_headers,
        json={"force_outcome": "succeeded"},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["status"] == "succeeded"
    assert body["paid_at"] is not None

    # Membership should now be active.
    mem = client.get(
        "/api/v1/memberships/me", headers=cust_headers
    ).json()
    me = next(m for m in mem["items"] if m["id"] == membership["id"])
    assert me["status"] == "active"


def test_verify_failure_leaves_membership_pending(
    client: TestClient, db_session
) -> None:
    h = admin_headers(db_session, "fail-admin@example.com")
    plan = _create_plan(client, h)
    cust = register_customer(client, email="failure@example.com")
    cust_headers = {"Authorization": f"Bearer {cust['access_token']}"}
    membership = _purchase_pending(client, cust_headers, plan["id"])

    checkout = client.post(
        "/api/v1/payments/checkout",
        headers=cust_headers,
        json={"membership_id": membership["id"], "provider": "mock"},
    ).json()
    payment_id = checkout["payment"]["id"]

    res = client.post(
        f"/api/v1/payments/{payment_id}/verify",
        headers=cust_headers,
        json={"force_outcome": "failed"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "failed"
    assert body["failure_reason"]

    mem = client.get(
        "/api/v1/memberships/me", headers=cust_headers
    ).json()
    me = next(m for m in mem["items"] if m["id"] == membership["id"])
    assert me["status"] == "pending"


def test_user_cannot_verify_another_users_payment(
    client: TestClient, db_session
) -> None:
    h = admin_headers(db_session, "cross-admin@example.com")
    plan = _create_plan(client, h)
    alice = register_customer(client, email="cross-alice@example.com")
    bob = register_customer(client, email="cross-bob@example.com")

    alice_headers = {"Authorization": f"Bearer {alice['access_token']}"}
    bob_headers = {"Authorization": f"Bearer {bob['access_token']}"}

    alice_membership = _purchase_pending(client, alice_headers, plan["id"])
    checkout = client.post(
        "/api/v1/payments/checkout",
        headers=alice_headers,
        json={"membership_id": alice_membership["id"], "provider": "mock"},
    ).json()
    payment_id = checkout["payment"]["id"]

    res = client.post(
        f"/api/v1/payments/{payment_id}/verify",
        headers=bob_headers,
        json={"force_outcome": "succeeded"},
    )
    assert res.status_code == 403


def test_me_lists_only_my_payments(client: TestClient, db_session) -> None:
    h = admin_headers(db_session, "listpay-admin@example.com")
    plan = _create_plan(client, h)
    alice = register_customer(client, email="alice-pays@example.com")
    bob = register_customer(client, email="bob-pays@example.com")
    alice_headers = {"Authorization": f"Bearer {alice['access_token']}"}
    bob_headers = {"Authorization": f"Bearer {bob['access_token']}"}

    alice_membership = _purchase_pending(client, alice_headers, plan["id"])
    bob_membership = _purchase_pending(client, bob_headers, plan["id"])
    client.post(
        "/api/v1/payments/checkout",
        headers=alice_headers,
        json={"membership_id": alice_membership["id"]},
    )
    client.post(
        "/api/v1/payments/checkout",
        headers=bob_headers,
        json={"membership_id": bob_membership["id"]},
    )

    alice_view = client.get("/api/v1/payments/me", headers=alice_headers).json()
    bob_view = client.get("/api/v1/payments/me", headers=bob_headers).json()
    assert alice_view["total"] == 1
    assert bob_view["total"] == 1
    assert alice_view["items"][0]["user_id"] != bob_view["items"][0]["user_id"]


def test_admin_can_list_all_payments(client: TestClient, db_session) -> None:
    h = admin_headers(db_session, "admin-all@example.com")
    plan = _create_plan(client, h)
    cust = register_customer(client, email="admin-list-cust@example.com")
    cust_headers = {"Authorization": f"Bearer {cust['access_token']}"}
    membership = _purchase_pending(client, cust_headers, plan["id"])
    client.post(
        "/api/v1/payments/checkout",
        headers=cust_headers,
        json={"membership_id": membership["id"]},
    )

    res = client.get("/api/v1/admin/payments", headers=h)
    assert res.status_code == 200
    body = res.json()
    assert body["total"] >= 1


def test_customer_cannot_list_all_payments(
    client: TestClient, db_session
) -> None:
    cust = register_customer(client, email="not-admin@example.com")
    cust_headers = {"Authorization": f"Bearer {cust['access_token']}"}
    res = client.get("/api/v1/admin/payments", headers=cust_headers)
    assert res.status_code == 403