"""Tests for customer membership purchase, renewal, and admin listings."""

from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient

from tests._helpers import admin_headers, register_customer


def _create_plan(
    client: TestClient, headers: dict, **overrides
) -> dict:
    body = {
        "name": "Monthly",
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


def test_customer_purchase_creates_pending_membership(
    client: TestClient, db_session
) -> None:
    h = admin_headers(db_session, "purchase-admin@example.com")
    plan = _create_plan(client, h)

    cust = register_customer(client, email="buyer@example.com")
    res = client.post(
        "/api/v1/memberships",
        headers={"Authorization": f"Bearer {cust['access_token']}"},
        json={"plan_id": plan["id"]},
    )
    assert res.status_code == 201
    body = res.json()
    assert body["plan_id"] == plan["id"]
    assert body["status"] == "pending"
    assert body["price_cents"] == plan["price_cents"]
    # 30 days from today.
    expected_end = date.today() + timedelta(days=30)
    assert body["end_date"] == expected_end.isoformat()


def test_customer_can_list_their_memberships(client: TestClient, db_session) -> None:
    h = admin_headers(db_session, "list-admin@example.com")
    plan = _create_plan(client, h)

    cust = register_customer(client, email="lister@example.com")
    headers = {"Authorization": f"Bearer {cust['access_token']}"}
    client.post("/api/v1/memberships", headers=headers, json={"plan_id": plan["id"]})

    res = client.get("/api/v1/memberships/me", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["plan_id"] == plan["id"]


def test_customer_can_renew(client: TestClient, db_session) -> None:
    h = admin_headers(db_session, "renew-admin@example.com")
    plan = _create_plan(client, h, duration_days=60)

    cust = register_customer(client, email="renewer@example.com")
    headers = {"Authorization": f"Bearer {cust['access_token']}"}
    first = client.post(
        "/api/v1/memberships", headers=headers, json={"plan_id": plan["id"]}
    ).json()

    res = client.post(
        f"/api/v1/memberships/{first['id']}/renew", headers=headers
    )
    assert res.status_code == 200
    body = res.json()
    # Renewal extends from the original end_date by 60 days.
    original_end = date.fromisoformat(first["end_date"])
    assert body["start_date"] == original_end.isoformat()
    assert body["end_date"] == (original_end + timedelta(days=60)).isoformat()


def test_purchase_unknown_plan_returns_404(client: TestClient) -> None:
    cust = register_customer(client, email="unknown@example.com")
    res = client.post(
        "/api/v1/memberships",
        headers={"Authorization": f"Bearer {cust['access_token']}"},
        json={"plan_id": 9999},
    )
    assert res.status_code == 404


def test_purchase_inactive_plan_returns_400(client: TestClient, db_session) -> None:
    h = admin_headers(db_session, "inactive-admin@example.com")
    plan = _create_plan(client, h, name="Soon Off", is_active=False)

    cust = register_customer(client, email="late@example.com")
    res = client.post(
        "/api/v1/memberships",
        headers={"Authorization": f"Bearer {cust['access_token']}"},
        json={"plan_id": plan["id"]},
    )
    assert res.status_code == 400


def test_renew_other_users_membership_returns_404(
    client: TestClient, db_session
) -> None:
    h = admin_headers(db_session, "other-admin@example.com")
    plan = _create_plan(client, h)

    a = register_customer(client, email="a@example.com")
    b = register_customer(client, email="b@example.com")
    first = client.post(
        "/api/v1/memberships",
        headers={"Authorization": f"Bearer {a['access_token']}"},
        json={"plan_id": plan["id"]},
    ).json()

    res = client.post(
        f"/api/v1/memberships/{first['id']}/renew",
        headers={"Authorization": f"Bearer {b['access_token']}"},
    )
    assert res.status_code == 404


def test_admin_expiring_lists_only_active_within_window(
    client: TestClient, db_session
) -> None:
    h = admin_headers(db_session, "exp-admin@example.com")
    short = _create_plan(client, h, name="Short", duration_days=2)
    long = _create_plan(client, h, name="Long", duration_days=60)

    cust = register_customer(client, email="expiring@example.com")
    ch = {"Authorization": f"Bearer {cust['access_token']}"}
    client.post("/api/v1/memberships", headers=ch, json={"plan_id": short["id"]})
    client.post("/api/v1/memberships", headers=ch, json={"plan_id": long["id"]})

    # Activate both via DB so status=active shows in the expiring query.
    from datetime import UTC, datetime

    from app.models.membership import Membership, MembershipStatus

    db_session.query(Membership).update(
        {Membership.status: MembershipStatus.ACTIVE, Membership.activated_at: datetime.now(UTC)}
    )
    db_session.commit()

    res = client.get("/api/v1/memberships/admin/expiring?days=7", headers=h)
    assert res.status_code == 200
    items = res.json()["items"]
    plan_ids = {item["plan_id"] for item in items}
    assert short["id"] in plan_ids
    assert long["id"] not in plan_ids


def test_admin_list_requires_admin(client: TestClient) -> None:
    cust = register_customer(client, email="plain@example.com")
    res = client.get(
        "/api/v1/memberships/admin/list",
        headers={"Authorization": f"Bearer {cust['access_token']}"},
    )
    assert res.status_code == 403
