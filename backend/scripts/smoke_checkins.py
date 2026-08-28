"""Live smoke test for Phase 5: card issuance, scan, replay, history."""

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
    admin_email = "smoke5-admin@example.com"
    admin_password = "adminpass123"
    res = client.post(
        "/auth/login",
        json={"email": admin_email, "password": admin_password},
    )
    if res.status_code != 200:
        # Try to seed the admin first.
        print("admin login failed; run: python -m app.scripts.seed_admin")
        sys.exit(1)
    a = {"Authorization": f"Bearer {res.json()['access_token']}"}

    # Create plan.
    res = client.post(
        "/plans/admin",
        headers=a,
        json={
            "name": "Smoke Checkin Plan",
            "duration_days": 30,
            "price_cents": 99000,
            "currency": "PHP",
            "is_active": True,
        },
    )
    _expect(res.status_code == 201, f"create plan -> {res.status_code}")
    plan_id = res.json()["id"]

    # Customer.
    cust_email = "smoke5-cust@example.com"
    res = client.post(
        "/auth/register",
        json={
            "email": cust_email,
            "password": "password123",
            "full_name": "Smoke Customer",
            "phone": "+639170000000",
        },
    )
    if res.status_code != 201:
        res = client.post(
            "/auth/login", json={"email": cust_email, "password": "password123"}
        )
    c = {"Authorization": f"Bearer {res.json()['access_token']}"}

    # Try to issue a card with no active membership → 404.
    res = client.get("/checkin/card", headers=c)
    _expect(res.status_code == 404, "card requires active membership")

    # Buy + activate.
    res = client.post("/memberships", headers=c, json={"plan_id": plan_id})
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

    # Issue card.
    res = client.get("/checkin/card", headers=c)
    _expect(res.status_code == 200, f"issue card -> {res.status_code}")
    card = res.json()
    _expect("." in card["token"], "token has JWT shape")
    token = card["token"]

    # Customer cannot scan.
    res = client.post("/checkin/scan", headers=c, json={"token": token})
    _expect(res.status_code == 403, "customer blocked from scanning")

    # Admin scans successfully.
    res = client.post("/checkin/scan", headers=a, json={"token": token, "source": "qr"})
    _expect(res.status_code == 200, f"scan happy -> {res.status_code}")
    _expect(res.json()["accepted"] is True, "scan accepted")

    # Replay rejected.
    res = client.post("/checkin/scan", headers=a, json={"token": token})
    _expect(res.status_code == 409, "replay blocked")

    # Bad token rejected.
    res = client.post("/checkin/scan", headers=a, json={"token": "garbage"})
    _expect(res.status_code == 400, "garbage token blocked")

    # Customer history has at least one entry.
    res = client.get("/checkin/me", headers=c)
    _expect(res.status_code == 200, "list my checkins")
    _expect(res.json()["total"] >= 1, "customer sees >=1 check-in")

    # Admin history for today.
    res = client.get("/admin/checkins", headers=a)
    _expect(res.status_code == 200, "admin list checkins")
    _expect(res.json()["total"] >= 1, "admin sees >=1 check-in")

    # Customer blocked from admin history.
    res = client.get("/admin/checkins", headers=c)
    _expect(res.status_code == 403, "customer blocked from admin checkins")

    print("\nALL PHASE 5 SMOKE TESTS PASSED")


if __name__ == "__main__":
    main()