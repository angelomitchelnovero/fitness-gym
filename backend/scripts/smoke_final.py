import json, urllib.request, urllib.error, os
from datetime import datetime, UTC

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

# DB setup for smoke users
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.core.security import hash_password

def setup_smoke_users():
    sess: Session = SessionLocal()
    admin_email = "smoke-admin@example.com"
    existing = sess.query(User).filter_by(email=admin_email).first()
    if existing is None:
        a = User(
            email=admin_email,
            password_hash=hash_password("adminpass123"),
            full_name="Smoke Admin",
            role=UserRole.ADMIN,
            is_active=True,
        )
        sess.add(a)
        sess.commit()
    else:
        existing.role = UserRole.ADMIN
        sess.commit()
    sess.close()

def test_step(name, fn):
    print(f"Testing {name}...", end=" ", flush=True)
    try:
        fn()
        print("✅")
    except Exception as e:
        print(f"❌\n  Error: {e}")
        raise e

def run_smoke():
    setup_smoke_users()

    # 1. Auth & Identity
    customer_email = f"smoke-cust-{int(datetime.now(UTC).timestamp())}@example.com"
    customer_pwd = "password123"

    def auth_phase():
        # Register Customer
        reg = call("POST", "/auth/register", {
            "email": customer_email,
            "password": customer_pwd,
            "full_name": "Smoke Customer",
            "phone": "+639170000001",
        })
        if "_status" in reg: raise Exception(f"Registration failed: {reg}")

        # Login Customer
        log = call("POST", "/auth/login", {"email": customer_email, "password": customer_pwd})
        if "_status" in log: raise Exception(f"Login failed: {log}")
        return log["access_token"]

    cust_token = None
    try:
        test_step("Customer Auth", lambda: None) # Placeholder if we can't return from lambda easily
        # Actually I'll just use a closure or variables
    except: pass

    # Let's just run them sequentially for simplicity
    print("--- STARTING COMPREHENSIVE SMOKE TEST ---")

    # Auth
    reg = call("POST", "/auth/register", {
        "email": customer_email,
        "password": customer_pwd,
        "full_name": "Smoke Customer",
        "phone": "+639170000001",
    })
    if "_status" in reg: print(f"❌ Register failed: {reg}"); return
    print("✅ Customer registered")

    log = call("POST", "/auth/login", {"email": customer_email, "password": customer_pwd})
    if "_status" in log: print(f"❌ Customer login failed: {log}"); return
    cust_token = log["access_token"]
    print("✅ Customer logged in")

    admin_log = call("POST", "/auth/login", {"email": "smoke-admin@example.com", "password": "adminpass123"})
    if "_status" in admin_log: print(f"❌ Admin login failed: {admin_log}"); return
    admin_token = admin_log["access_token"]
    print("✅ Admin logged in")

    # Plans
    plan_name = f"Smoke Plan {int(datetime.now(UTC).timestamp())}"
    plan = call("POST", "/plans/admin", {
        "name": plan_name,
        "description": "Smoke test plan",
        "price_cents": 5000,
        "duration_days": 30
    }, token=admin_token)
    if "_status" in plan: print(f"❌ Admin create plan failed: {plan}"); return
    plan_id = plan["id"]
    print(f"✅ Plan created: {plan_id}")

    plans_list = call("GET", "/plans", token=cust_token)
    if "_status" in plans_list or not any(p["name"] == plan_name for p in plans_list.get("items", [])):
        print(f"❌ Customer cannot see plan: {plans_list}"); return
    print("✅ Customer sees plans")

    # Payments & Memberships
    mem_req = call("POST", "/memberships", {"plan_id": plan_id}, token=cust_token)
    if "_status" in mem_req: print(f"❌ Membership purchase failed: {mem_req}"); return
    membership_id = mem_req["id"]
    print(f"✅ Membership created: {membership_id}")

    checkout = call("POST", "/payments/checkout", {"membership_id": membership_id}, token=cust_token)
    if "_status" in checkout: print(f"❌ Checkout failed: {checkout}"); return
    payment_id = checkout["payment"]["id"]
    print(f"✅ Checkout initiated: {payment_id}")

    # Verify payment (mock success)
    verify = call("POST", f"/payments/{payment_id}/verify", token=cust_token)
    if "_status" in verify: print(f"❌ Payment verification failed: {verify}"); return
    print("✅ Payment verified")

    mem = call("GET", "/memberships/me", token=cust_token)
    if "_status" in mem or not any(m["status"] == "active" for m in mem["items"]):
        print(f"❌ Membership not active: {mem}"); return
    print("✅ Membership active")

    # Check-in
    card = call("GET", "/checkin/card", token=cust_token)
    if "_status" in card or "token" not in card: print(f"❌ Card generation failed: {card}"); return
    qr_token = card["token"]
    print("✅ Check-in card generated")

    scan = call("POST", "/checkin/scan", {"token": qr_token}, token=admin_token)
    if "_status" in scan or not scan.get("accepted"): print(f"❌ Check-in scan failed: {scan}"); return
    print("✅ Check-in scan successful")

    history = call("GET", "/checkin/me", token=cust_token)
    if "_status" in history or not history: print(f"❌ Check-in history empty: {history}"); return
    print("✅ Check-in history updated")

    # Dashboards & Reports
    cust_dash = call("GET", "/dashboard/me", token=cust_token)
    if "_status" in cust_dash: print(f"❌ Customer dashboard failed: {cust_dash}"); return
    print("✅ Customer dashboard accessed")

    admin_dash = call("GET", "/admin/dashboard", token=admin_token)
    if "_status" in admin_dash: print(f"❌ Admin dashboard failed: {admin_dash}"); return
    print("✅ Admin dashboard accessed")

    reports = call("GET", "/admin/reports?period=week", token=admin_token)
    if "_status" in reports: print(f"❌ Reports failed: {reports}"); return
    print("✅ Reports accessed")

    print("\n--- ALL SMOKE TESTS PASSED SUCCESSFULLY ---")

if __name__ == "__main__":
    run_smoke()
