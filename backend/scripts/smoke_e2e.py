#!/usr/bin/env python
"""End-to-end smoke against a running backend.

Walks a single member through every phase:
  register -> buy plan -> checkout -> verify payment -> issue QR ->
  scan -> read history -> admin dashboard -> admin reports ->
  notifications inbox -> expire-soon reminder.

Run with the backend on http://127.0.0.1:8000 and the dev DB seeded
(`ADMIN_PASSWORD=adminpass123 .venv/bin/python scripts/seed_admin.py`).
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000/api/v1"


def call(method, path, data=None, token=None):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(data).encode() if data is not None else None,
        method=method,
        headers={
            "Content-Type": "application/json",
            **({"Authorization": "Bearer " + token} if token else {}),
        },
    )
    try:
        return json.loads(urllib.request.urlopen(req).read())
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read())
        except Exception:
            body = e.read().decode(errors="ignore")
        return {"_status": e.code, "_body": body}


def step(label: str, ok: bool, detail: str = "") -> None:
    mark = "OK " if ok else "FAIL"
    print(f"  [{mark}] {label}{(' — ' + detail) if detail else ''}")
    if not ok:
        sys.exit(1)


print("== E2E smoke ==")

# --- 1+2: admin login (Phase 2)
admin = call("POST", "/auth/login",
             {"email": "admin@example.com", "password": "adminpass123"})
step("admin login", "access_token" in admin, f"role={admin.get('role', '?')}")
admin_tok = admin["access_token"]

# Create a plan (Phase 3)
plan = call("POST", "/plans/admin", {
    "name": "E2E Monthly",
    "description": "Phase 10 walkthrough plan",
    "duration_days": 30,
    "price_cents": 120000,
    "currency": "PHP",
    "is_active": True,
}, token=admin_tok)
step("create plan (admin)", isinstance(plan, dict) and "id" in plan,
     f"plan_id={plan.get('id')}")
plan_id = plan["id"]

# --- Phase 2: customer registers
import secrets
suffix = secrets.token_hex(4)
customer = call("POST", "/auth/register", {
    "email": f"e2e-{suffix}@example.com",
    "password": "password123",
    "full_name": "E2E Walker",
    "phone": "+639170000002",
})
step("customer register", "access_token" in customer)
cust_tok = customer["access_token"]

# --- Phase 3: purchase membership
mem = call("POST", "/memberships", {"plan_id": plan_id}, token=cust_tok)
step("purchase membership", mem.get("status") == "pending",
     f"membership_id={mem.get('id')}")
mem_id = mem["id"]

# --- Phase 4: checkout + verify
co = call("POST", "/payments/checkout",
          {"membership_id": mem_id, "provider": "mock"}, token=cust_tok)
pay_id = co["payment"]["id"]
verify = call("POST", f"/payments/{pay_id}/verify",
              {"force_outcome": "succeeded"}, token=cust_tok)
step("verify payment → active", verify.get("status") == "succeeded")

# --- Phase 5: card issue + QR scan + history
card = call("GET", "/checkin/card", token=cust_tok)
step("issue QR card", "token" in card and "membership_id" in card,
     f"expires_at={card.get('expires_at')}")
scan = call("POST", "/checkin/scan",
            {"token": card["token"]}, token=admin_tok)
step("admin scan accepts customer", scan.get("accepted") is True,
     f"reason={scan.get('reason')}")
hist = call("GET", "/checkin/me", token=cust_tok)
step("check-in history lists 1 entry", hist.get("total") == 1)

# Replay protection
replay = call("POST", "/checkin/scan",
              {"token": card["token"]}, token=admin_tok)
step("QR replay is rejected", replay.get("_status") in (400, 409))

# --- Phase 6: admin dashboard
dash = call("GET", "/admin/dashboard", token=admin_tok)
step("admin dashboard reachable",
     "active_memberships" in dash and "total_revenue_cents" in dash,
     f"revenue={dash.get('total_revenue_cents')}")

# --- Phase 7: customer dashboard
cdash = call("GET", "/dashboard/me", token=cust_tok)
step("customer dashboard reachable",
     "active_membership" in cdash and "recent_payments" in cdash)

# --- Phase 8: notifications inbox
notifs = call("GET", "/notifications/me", token=cust_tok)
kinds = [n["kind"] for n in notifs.get("items", [])]
step("notifications inbox has at least one payment receipt",
     "payment_receipt" in kinds and "checkin_confirmation" in kinds,
     f"total={notifs.get('total')} kinds={kinds}")
expire = call("POST", "/admin/notifications/expire-soon?days=7",
              token=admin_tok)
step("expire-soon endpoint reachable",
     "sent" in expire, f"sent={expire.get('sent')}")

# --- Phase 9: reports
rep = call("GET", "/admin/reports?period=week&bucket=day", token=admin_tok)
step("admin reports reachable",
     "revenue_by_period" in rep and "popular_plans" in rep and
     "retention" in rep)

print("\n== E2E smoke: ALL OK ==")
