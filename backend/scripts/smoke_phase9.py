import json, urllib.request, urllib.error

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


# Promote a smoke admin via DB
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.core.security import hash_password

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

res = call("POST", "/auth/login", {"email": admin_email, "password": "adminpass123"})
tok = res["access_token"]

print("=== week / day ===")
b = call("GET", "/admin/reports?period=week&bucket=day", token=tok)
print(" period:", b["period"], "bucket:", b["bucket_size"], "currency:", b["currency"])
print(" buckets:", len(b["revenue_by_period"]))
print(" retention:", b["retention"])
print(" popular:", len(b["popular_plans"]))

print("=== month / week ===")
b = call("GET", "/admin/reports?period=month&bucket=week", token=tok)
print(" buckets:", len(b["revenue_by_period"]))

print("=== period=day ===")
b = call("GET", "/admin/reports?period=day", token=tok)
print(" buckets:", len(b["revenue_by_period"]))

print("=== invalid period=year ===")
res = call("GET", "/admin/reports?period=year", token=tok)
print(" status:", res.get("_status"))

# Customer forbidden
c = call("POST", "/auth/register", {
    "email": "smoke-cust9@example.com",
    "password": "password123",
    "full_name": "Smoke Cust",
    "phone": "+639170000001",
})
res = call("GET", "/admin/reports", token=c["access_token"])
print("=== customer forbidden ===")
print(" status:", res.get("_status"))
