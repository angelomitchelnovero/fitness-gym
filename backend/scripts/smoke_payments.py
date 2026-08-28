"""Quick live smoke test for the Phase 4 payment flow.

Walks: admin login → create plan → customer register → purchase membership
→ checkout → verify (success) → re-read membership (must be active).
Also: customer cannot verify another customer's payment.
Exits non-zero on any failure.
"""

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

    # 1. Admin login.
    admin_email = "smoke-admin@example.com"
    admin_password = "adminpass123"
    res = client.post(
        "/auth/login",
        json={"email": admin_email, "password": admin_password},
    )
    if res.status_code != 200:
        # Admin may not exist — register one as a real admin via users admin route.
        # The bootstrap admin is created via seed, so this should succeed.
        print("admin login failed:", res.status_code, res.text)
        sys.exit(1)
    admin_token = res.json()["access_token"]
    a = {"Authorization": f"Bearer {admin_token}"}
    _expect(True, "admin logged in")

    # 2. Create plan.
    res = client.post(
        "/plans/admin",
        headers=a,
        json={
            "name": "Smoke Plan",
            "description": "for live test",
            "duration_days": 30,
            "price_cents": 99000,
            "currency": "PHP",
            "is_active": True,
        },
    )
    _expect(res.status_code == 201, f"create plan -> {res.status_code}")
    plan_id = res.json()["id"]

    # 3. Customer register.
    cust_email = "smoke-cust@example.com"
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
        # Already registered from a prior run — fall through to login.
        res = client.post(
            "/auth/login",
            json={"email": cust_email, "password": "password123"},
        )
        _expect(res.status_code == 200, f"customer auth -> {res.status_code}")
    cust_token = res.json()["access_token"]
    c = {"Authorization": f"Bearer {cust_token}"}
    _expect(True, "customer authed")

    # 4. Purchase pending membership.
    res = client.post("/memberships", headers=c, json={"plan_id": plan_id})
    _expect(res.status_code == 201, f"purchase membership -> {res.status_code}")
    membership_id = res.json()["id"]
    _expect(res.json()["status"] == "pending", "membership starts pending")

    # 5. Checkout.
    res = client.post(
        "/payments/checkout",
        headers=c,
        json={"membership_id": membership_id, "provider": "mock"},
    )
    _expect(res.status_code == 201, f"checkout -> {res.status_code}")
    payment = res.json()["payment"]
    _expect(payment["status"] == "pending", "payment starts pending")
    _expect(payment["external_id"].startswith("pi_mock_"), "external id issued")
    payment_id = payment["id"]

    # 6. Verify (succeeded).
    res = client.post(
        f"/payments/{payment_id}/verify",
        headers=c,
        json={"force_outcome": "succeeded"},
    )
    _expect(res.status_code == 200, f"verify success -> {res.status_code}")
    _expect(res.json()["status"] == "succeeded", "payment marked succeeded")
    _expect(res.json()["paid_at"] is not None, "paid_at set")

    # 7. Membership should now be active.
    res = client.get("/memberships/me", headers=c)
    _expect(res.status_code == 200, "list memberships")
    me = next(m for m in res.json()["items"] if m["id"] == membership_id)
    _expect(me["status"] == "active", "membership activated")
    _expect(me["activated_at"] is not None, "activated_at set")

    # 8. Cross-user protection: a second customer must not verify first's payment.
    other_email = "smoke-other@example.com"
    res = client.post(
        "/auth/register",
        json={
            "email": other_email,
            "password": "password123",
            "full_name": "Other Customer",
            "phone": "+639170000001",
        },
    )
    if res.status_code != 201:
        res = client.post(
            "/auth/login",
            json={"email": other_email, "password": "password123"},
        )
    other_token = res.json()["access_token"]
    o = {"Authorization": f"Bearer {other_token}"}

    # Make a fresh pending payment from the original customer.
    res = client.post("/memberships", headers=c, json={"plan_id": plan_id})
    new_membership_id = res.json()["id"]
    res = client.post(
        "/payments/checkout",
        headers=c,
        json={"membership_id": new_membership_id, "provider": "mock"},
    )
    new_payment_id = res.json()["payment"]["id"]

    res = client.post(
        f"/payments/{new_payment_id}/verify",
        headers=o,
        json={"force_outcome": "succeeded"},
    )
    _expect(res.status_code == 403, f"cross-user verify blocked -> {res.status_code}")

    # 9. Verify failure path leaves membership pending.
    res = client.post(
        f"/payments/{new_payment_id}/verify",
        headers=c,
        json={"force_outcome": "failed"},
    )
    _expect(res.status_code == 200, "verify failure -> 200")
    _expect(res.json()["status"] == "failed", "payment marked failed")
    res = client.get("/memberships/me", headers=c)
    me = next(m for m in res.json()["items"] if m["id"] == new_membership_id)
    _expect(me["status"] == "pending", "membership stays pending on failure")

    # 10. Admin can list all payments.
    res = client.get("/admin/payments", headers=a)
    _expect(res.status_code == 200, "admin list payments")
    _expect(res.json()["total"] >= 2, "admin sees >=2 payments")

    # 11. Customer cannot list all payments.
    res = client.get("/admin/payments", headers=c)
    _expect(res.status_code == 403, "customer blocked from admin list")

    print("\nALL SMOKE TESTS PASSED")


if __name__ == "__main__":
    main()