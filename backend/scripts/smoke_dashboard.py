"""Quick live smoke test for Phase 6 admin dashboard endpoint."""

from __future__ import annotations

import sys

import httpx

BASE = "http://127.0.0.1:8000/api/v1"
TIMEOUT = 5.0


def _expect(cond: bool, msg: str) -> None:
    print(("✓ " if cond else "✗ ") + msg)
    if not cond:
        sys.exit(1)


def main() -> None:
    client = httpx.Client(base_url=BASE, timeout=TIMEOUT)

    # Admin login.
    res = client.post(
        "/auth/login",
        json={"email": "smoke6-admin@example.com", "password": "adminpass123"},
    )
    _expect(res.status_code == 200, "admin logged in")
    a = {"Authorization": f"Bearer {res.json()['access_token']}"}

    # Customer.
    cust_email = "smoke6-cust@example.com"
    res = client.post(
        "/auth/register",
        json={
            "email": cust_email,
            "password": "password123",
            "full_name": "Dash Smoke",
            "phone": "+639170000000",
        },
    )
    if res.status_code != 201:
        res = client.post(
            "/auth/login", json={"email": cust_email, "password": "password123"}
        )
    c = {"Authorization": f"Bearer {res.json()['access_token']}"}

    # Create plan and an active member to give the dashboard something to count.
    res = client.post(
        "/plans/admin",
        headers=a,
        json={
            "name": "Dashboard Smoke Plan",
            "duration_days": 30,
            "price_cents": 99000,
            "currency": "PHP",
            "is_active": True,
        },
    )
    _expect(res.status_code == 201, "create plan")
    plan_id = res.json()["id"]

    res = client.post(
        "/memberships", headers=c, json={"plan_id": plan_id}
    )
    membership_id = res.json()["id"]
    res = client.post(
        "/payments/checkout",
        headers=c,
        json={"membership_id": membership_id, "provider": "mock"},
    )
    payment_id = res.json()["payment"]["id"]
    client.post(
        f"/payments/{payment_id}/verify",
        headers=c,
        json={"force_outcome": "succeeded"},
    )

    # Issue card + check the customer in for today's stats.
    card = client.get("/checkin/card", headers=c).json()
    client.post("/checkin/scan", headers=a, json={"token": card["token"]})

    # Customer blocked from dashboard.
    res = client.get("/admin/dashboard", headers=c)
    _expect(res.status_code == 403, "customer blocked from admin dashboard")

    # Admin gets summary with all keys.
    res = client.get("/admin/dashboard", headers=a)
    _expect(res.status_code == 200, "admin dashboard returns 200")
    body = res.json()
    for key in (
        "active_memberships",
        "pending_memberships",
        "expiring_within_days",
        "today_checkins_total",
        "today_checkins_accepted",
        "total_revenue_cents",
        "currency",
        "plan_breakdown",
        "recent_payments",
        "recent_memberships",
    ):
        _expect(key in body, f"key present: {key}")
    _expect(body["active_memberships"] >= 1, "counts active memberships")
    _expect(body["today_checkins_total"] >= 1, "counts today's check-ins")
    _expect(
        body["total_revenue_cents"] >= 99000,
        "revenue includes the new payment",
    )
    _expect(
        any(p["plan_id"] == plan_id for p in body["plan_breakdown"]),
        "plan breakdown includes the new plan",
    )
    _expect(
        any(m["id"] == membership_id for m in body["recent_memberships"]),
        "recent memberships includes the new membership",
    )

    print("\nALL PHASE 6 SMOKE TESTS PASSED")


if __name__ == "__main__":
    main()