"""Quick live smoke for Phase 7: GET /dashboard/me."""

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

    res = client.post(
        "/auth/login",
        json={"email": "smoke7-admin@example.com", "password": "adminpass123"},
    )
    _expect(res.status_code == 200, "admin logged in")
    a = {"Authorization": f"Bearer {res.json()['access_token']}"}

    cust_email = "smoke7-cust@example.com"
    res = client.post(
        "/auth/register",
        json={
            "email": cust_email,
            "password": "password123",
            "full_name": "Phase 7 Customer",
            "phone": "+639170000000",
        },
    )
    if res.status_code != 201:
        res = client.post(
            "/auth/login", json={"email": cust_email, "password": "password123"}
        )
    c = {"Authorization": f"Bearer {res.json()['access_token']}"}

    # Baseline (no membership, no payments, no checkins).
    res = client.get("/dashboard/me", headers=c)
    _expect(res.status_code == 200, "dashboard returns 200")
    body = res.json()
    _expect(body["active_membership"] is None, "no active membership yet")
    _expect(body["spend_total_cents"] == 0, "no spend yet")
    _expect(body["recent_payments"] == [], "no payments yet")
    _expect(body["recent_checkins"] == [], "no check-ins yet")

    # Set up plan + active membership + check-in.
    res = client.post(
        "/plans/admin",
        headers=a,
        json={
            "name": "P7 Plan",
            "duration_days": 30,
            "price_cents": 149000,
            "currency": "PHP",
            "is_active": True,
        },
    )
    plan_id = res.json()["id"]
    res = client.post("/memberships", headers=c, json={"plan_id": plan_id})
    mid = res.json()["id"]
    res = client.post(
        "/payments/checkout",
        headers=c,
        json={"membership_id": mid, "provider": "mock"},
    )
    pid = res.json()["payment"]["id"]
    client.post(
        f"/payments/{pid}/verify",
        headers=c,
        json={"force_outcome": "succeeded"},
    )
    card = client.get("/checkin/card", headers=c).json()
    client.post("/checkin/scan", headers=a, json={"token": card["token"]})

    res = client.get("/dashboard/me", headers=c)
    body = res.json()
    _expect(body["active_membership"] is not None, "active membership present")
    _expect(body["active_membership"]["status"] == "active", "active status")
    _expect(body["spend_total_cents"] >= 149000, "spend reflects payment")
    _expect(
        body["spend_30d_cents"] >= 149000, "30-day spend reflects payment"
    )
    _expect(len(body["recent_payments"]) >= 1, "recent payments populated")
    _expect(len(body["recent_checkins"]) >= 1, "recent checkins populated")
    _expect(body["recent_checkins"][0]["accepted"] is True, "last checkin admitted")
    _expect(body["user"]["email"] == cust_email, "user echo")

    # Admin can also call (it's just their own dashboard; we don't restrict).
    res = client.get("/dashboard/me", headers=a)
    _expect(res.status_code == 200, "admin can also fetch their dashboard")

    # Unauthenticated → 401.
    res = client.get("/dashboard/me")
    _expect(res.status_code == 401, "unauthenticated blocked")

    print("\nALL PHASE 7 SMOKE TESTS PASSED")


if __name__ == "__main__":
    main()