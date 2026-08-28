"""Tests for the admin reports endpoint (Phase 9)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.payment import Payment, PaymentStatus
from app.models.user import User, UserRole
from tests._helpers import admin_headers, register_customer


def _plan(client: TestClient, admin_h: dict, **overrides) -> dict:
    body = {
        "name": "Reports Plan",
        "description": "for reports tests",
        "duration_days": 30,
        "price_cents": 99000,
        "currency": "PHP",
        "is_active": True,
    }
    body.update(overrides)
    res = client.post("/api/v1/plans/admin", headers=admin_h, json=body)
    assert res.status_code == 201, res.text
    return res.json()


def _buy_and_pay_succeeded(
    client: TestClient, cust_h: dict, plan_id: int
) -> int:
    res = client.post(
        "/api/v1/memberships", headers=cust_h, json={"plan_id": plan_id}
    )
    assert res.status_code == 201, res.text
    mem = res.json()
    res = client.post(
        "/api/v1/payments/checkout",
        headers=cust_h,
        json={"membership_id": mem["id"], "provider": "mock"},
    )
    assert res.status_code == 201, res.text
    payment_id = res.json()["payment"]["id"]
    res = client.post(
        f"/api/v1/payments/{payment_id}/verify",
        headers=cust_h,
        json={"force_outcome": "succeeded"},
    )
    assert res.status_code == 200, res.text
    return mem["id"]


def _make_user(db: Session, email: str, role: UserRole = UserRole.CUSTOMER) -> User:
    u = User(
        email=email,
        password_hash=hash_password("password123"),
        full_name=email.split("@")[0],
        role=role,
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _seed_payment(
    db: Session,
    *,
    user_id: int,
    membership_id: int | None,
    amount_cents: int,
    paid_at: datetime,
) -> Payment:
    p = Payment(
        user_id=user_id,
        membership_id=membership_id,
        amount_cents=amount_cents,
        currency="PHP",
        provider="mock",
        external_id=f"pi_seed_{paid_at.isoformat()}",
        status=PaymentStatus.SUCCEEDED,
        paid_at=paid_at,
        method="card",
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


# ------------------------------- basics -------------------------------


def test_reports_requires_admin(client: TestClient, db_session) -> None:
    cust = register_customer(client, email="report-cust@example.com")
    cust_h = {"Authorization": f"Bearer {cust['access_token']}"}
    res = client.get("/api/v1/admin/reports", headers=cust_h)
    assert res.status_code == 403


def test_reports_returns_baseline_shape(
    client: TestClient, db_session
) -> None:
    h = admin_headers(db_session, "rep-base-admin@example.com")
    res = client.get("/api/v1/admin/reports", headers=h)
    assert res.status_code == 200, res.text
    body = res.json()
    for k in (
        "period",
        "bucket_size",
        "currency",
        "revenue_by_period",
        "popular_plans",
        "retention",
    ):
        assert k in body, f"missing key: {k}"
    # Retention has the expected shape.
    for k in (
        "active", "cancelled", "expired", "pending",
        "total_lifetime", "churn_rate",
    ):
        assert k in body["retention"], f"missing retention key: {k}"


# ----------------------------- bucketing -----------------------------


def test_reports_week_buckets_default_to_day(
    client: TestClient, db_session
) -> None:
    h = admin_headers(db_session, "rep-week-admin@example.com")
    res = client.get("/api/v1/admin/reports?period=week", headers=h)
    assert res.status_code == 200, res.text
    body = res.json()
    # 7 buckets by default.
    assert len(body["revenue_by_period"]) == 7


def test_reports_revenue_aggregates_into_bucket(
    client: TestClient, db_session
) -> None:
    """Succeeded payments inside the window must sum into buckets."""
    h = admin_headers(db_session, "rep-sum-admin@example.com")
    plan = _plan(client, h)
    cust = register_customer(client, email="rep-sum@example.com")
    cust_h = {"Authorization": f"Bearer {cust['access_token']}"}
    mem_id = _buy_and_pay_succeeded(client, cust_h, plan["id"])

    # Add a second direct (not via /payments) payment backdated 1 day.
    today = datetime.now(UTC)
    me = client.get("/api/v1/auth/me", headers=cust_h).json()
    _seed_payment(
        db_session,
        user_id=me["id"],
        membership_id=None,
        amount_cents=5000,
        paid_at=today - timedelta(days=1),
    )

    res = client.get(
        "/api/v1/admin/reports?period=week&bucket=day", headers=h
    )
    body = res.json()
    total = sum(point["revenue_cents"] for point in body["revenue_by_period"])
    # First plan (99000) + 5000 backdated.
    assert total >= 99000 + 5000
    # The latest bucket must contain at least the 99000 plan payment.
    assert (
        sorted(body["revenue_by_period"], key=lambda p: p["period_start"])[-1][
            "revenue_cents"
        ]
        >= 99000
    )
    assert mem_id  # sanity — used to silence unused-binding lint


def test_reports_period_day_returns_single_point(
    client: TestClient, db_session
) -> None:
    h = admin_headers(db_session, "rep-day-admin@example.com")
    res = client.get("/api/v1/admin/reports?period=day", headers=h)
    body = res.json()
    assert len(body["revenue_by_period"]) == 1
    assert body["bucket_size"] == "day"


# ---------------------------- retention ----------------------------


def test_reports_retention_counts_reflect_data(
    client: TestClient, db_session
) -> None:
    h = admin_headers(db_session, "rep-ret-admin@example.com")
    plan = _plan(client, h)
    alice = register_customer(client, email="ret-alice@example.com")
    bob = register_customer(client, email="ret-bob@example.com")
    alice_h = {"Authorization": f"Bearer {alice['access_token']}"}
    bob_h = {"Authorization": f"Bearer {bob['access_token']}"}
    # Alice: ACTIVE
    _buy_and_pay_succeeded(client, alice_h, plan["id"])
    # Bob: PENDING (no payment)
    res = client.post(
        "/api/v1/memberships", headers=bob_h, json={"plan_id": plan["id"]}
    )
    assert res.status_code == 201

    res = client.get("/api/v1/admin/reports", headers=h)
    body = res.json()
    assert body["retention"]["active"] >= 1
    assert body["retention"]["pending"] >= 1
    assert body["retention"]["total_lifetime"] >= 1
    assert 0.0 <= body["retention"]["churn_rate"] <= 1.0


# ---------------------------- popular plans ----------------------------


def test_reports_popular_plans_orders_by_active_count(
    client: TestClient, db_session
) -> None:
    h = admin_headers(db_session, "rep-pop-admin@example.com")
    # Two plans; cheaper one gets more active subs.
    cheap = _plan(client, h, name="Cheap", price_cents=10000)
    pricey = _plan(client, h, name="Pricey", price_cents=99900)

    # 2 customers on cheap, 1 on pricey.
    for i in range(2):
        cust = register_customer(client, email=f"cheap-{i}@example.com")
        cust_h = {"Authorization": f"Bearer {cust['access_token']}"}
        _buy_and_pay_succeeded(client, cust_h, cheap["id"])
    cust = register_customer(client, email="pricey-0@example.com")
    cust_h = {"Authorization": f"Bearer {cust['access_token']}"}
    _buy_and_pay_succeeded(client, cust_h, pricey["id"])

    res = client.get("/api/v1/admin/reports", headers=h)
    body = res.json()
    names = [p["plan_name"] for p in body["popular_plans"]]
    assert names[0] == "Cheap"
    assert body["popular_plans"][0]["active_members"] >= 2


# ---------------------------- validation ----------------------------


def test_reports_rejects_bad_period(
    client: TestClient, db_session
) -> None:
    h = admin_headers(db_session, "rep-bad-admin@example.com")
    res = client.get("/api/v1/admin/reports?period=year", headers=h)
    assert res.status_code == 422
    res = client.get("/api/v1/admin/reports?bucket=hour", headers=h)
    assert res.status_code == 422


def _buy_and_pay_succeeded_check(*_args, **_kwargs):  # silence unused
    return None