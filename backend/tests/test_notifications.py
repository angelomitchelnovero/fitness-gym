"""Tests for the notifications system (Phase 8).

Covers:
  * payment receipt is enqueued on successful verify
  * expiry reminders target only soon-to-expire active memberships
  * failed channel sends record a FAILED notification row
  * /notifications/me is scoped to the caller
  * admin trigger endpoint requires admin role
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.membership import Membership, MembershipStatus
from app.models.notification import Notification, NotificationKind, NotificationStatus
from app.models.user import User, UserRole
from app.services.notifications.base import DeliveryResult
from tests._helpers import admin_headers, register_customer


def _plan(client: TestClient, admin_h: dict, **overrides) -> dict:
    body = {
        "name": "Notify Plan",
        "description": "for notifications tests",
        "duration_days": 30,
        "price_cents": 50000,
        "currency": "PHP",
        "is_active": True,
    }
    body.update(overrides)
    res = client.post("/api/v1/plans/admin", headers=admin_h, json=body)
    assert res.status_code == 201, res.text
    return res.json()


def _active_membership(
    db: Session, *, user_id: int, plan_id: int, end: date
) -> Membership:
    """Insert an ACTIVE membership with a chosen `end_date`."""
    m = Membership(
        user_id=user_id,
        plan_id=plan_id,
        start_date=date.today(),
        end_date=end,
        status=MembershipStatus.ACTIVE,
        price_cents=50000,
        currency="PHP",
        activated_at=datetime.now(UTC),
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def _buy_and_pay(
    client: TestClient, cust_h: dict, plan_id: int
) -> dict:
    """Purchase a membership and force-verify a payment (returns membership row)."""
    res = client.post(
        "/api/v1/memberships", headers=cust_h, json={"plan_id": plan_id}
    )
    assert res.status_code == 201, res.text
    membership = res.json()
    res = client.post(
        "/api/v1/payments/checkout",
        headers=cust_h,
        json={"membership_id": membership["id"], "provider": "mock"},
    )
    assert res.status_code == 201, res.text
    payment_id = res.json()["payment"]["id"]
    res = client.post(
        f"/api/v1/payments/{payment_id}/verify",
        headers=cust_h,
        json={"force_outcome": "succeeded"},
    )
    assert res.status_code == 200, res.text
    return membership


# ----------------------------- payment receipt -----------------------------


def test_payment_receipt_is_enqueued(
    client: TestClient, db_session
) -> None:
    admin_h = admin_headers(db_session, "rcpt-admin@example.com")
    plan = _plan(client, admin_h)
    cust = register_customer(client, email="rcpt-cust@example.com")
    cust_h = {"Authorization": f"Bearer {cust['access_token']}"}

    _buy_and_pay(client, cust_h, plan["id"])

    rows = db_session.scalars(
        select(Notification).where(
            Notification.kind == NotificationKind.PAYMENT_RECEIPT
        )
    ).all()
    assert len(rows) == 1
    notif = rows[0]
    assert notif.status == NotificationStatus.SENT
    assert notif.recipient == "rcpt-cust@example.com"
    assert notif.related_payment_id is not None
    assert "Payment received" in notif.subject


def test_payment_receipt_not_enqueued_on_failure(
    client: TestClient, db_session
) -> None:
    admin_h = admin_headers(db_session, "rcptfail-admin@example.com")
    plan = _plan(client, admin_h)
    cust = register_customer(client, email="rcptfail-cust@example.com")
    cust_h = {"Authorization": f"Bearer {cust['access_token']}"}

    res = client.post(
        "/api/v1/memberships", headers=cust_h, json={"plan_id": plan["id"]}
    )
    assert res.status_code == 201
    mem = res.json()
    res = client.post(
        "/api/v1/payments/checkout",
        headers=cust_h,
        json={"membership_id": mem["id"], "provider": "mock"},
    )
    payment_id = res.json()["payment"]["id"]
    client.post(
        f"/api/v1/payments/{payment_id}/verify",
        headers=cust_h,
        json={"force_outcome": "failed"},
    )

    rows = db_session.scalars(
        select(Notification).where(
            Notification.kind == NotificationKind.PAYMENT_RECEIPT
        )
    ).all()
    assert rows == []


# -------------------------- failed channel send --------------------------


def test_failed_channel_marks_row_failed(
    client: TestClient, db_session
) -> None:
    admin_h = admin_headers(db_session, "failchan-admin@example.com")
    plan = _plan(client, admin_h)
    cust = register_customer(client, email="failchan-cust@example.com")
    cust_h = {"Authorization": f"Bearer {cust['access_token']}"}
    membership = _buy_and_pay(client, cust_h, plan["id"])

    # The trigger has already been called once and recorded success.
    # Reset state, then patch the channel to fail and verify again on a
    # fresh payment.
    res = client.post(
        "/api/v1/memberships", headers=cust_h, json={"plan_id": plan["id"]}
    )
    mem = res.json()
    res = client.post(
        "/api/v1/payments/checkout",
        headers=cust_h,
        json={"membership_id": mem["id"], "provider": "mock"},
    )
    payment_id = res.json()["payment"]["id"]

    with patch(
        "app.services.notification_service.get_channel",
        return_value=_BoomChannel(),
    ):
        res = client.post(
            f"/api/v1/payments/{payment_id}/verify",
            headers=cust_h,
            json={"force_outcome": "succeeded"},
        )
        assert res.status_code == 200, res.text

    rows = db_session.scalars(
        select(Notification).where(
            Notification.related_payment_id == payment_id,
            Notification.kind == NotificationKind.PAYMENT_RECEIPT,
        )
    ).all()
    assert len(rows) == 1
    assert rows[0].status == NotificationStatus.FAILED
    assert "boom" in (rows[0].error or "")
    assert membership["id"] > 0  # existing variable used; suppress lint


class _BoomChannel:
    name = "boom"
    _DELIVERY = DeliveryResult  # captured from outer scope at class-eval time

    def send(self, message):  # noqa: D401 - test double
        return self._DELIVERY(ok=False, error="simulated boom")


# -------------------------- /notifications/me --------------------------


def test_my_notifications_scoped_to_caller(
    client: TestClient, db_session
) -> None:
    admin_h = admin_headers(db_session, "scope-admin@example.com")
    plan = _plan(client, admin_h)
    alice = register_customer(client, email="alice-scope@example.com")
    bob = register_customer(client, email="bob-scope@example.com")
    alice_h = {"Authorization": f"Bearer {alice['access_token']}"}
    bob_h = {"Authorization": f"Bearer {bob['access_token']}"}
    _buy_and_pay(client, alice_h, plan["id"])
    _buy_and_pay(client, bob_h, plan["id"])

    res = client.get("/api/v1/notifications/me", headers=alice_h)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["total"] == 1
    assert body["items"][0]["recipient"] == "alice-scope@example.com"

    res = client.get("/api/v1/notifications/me", headers=bob_h)
    body = res.json()
    assert body["total"] == 1
    assert body["items"][0]["recipient"] == "bob-scope@example.com"


# ---------------------------- expire-soon ----------------------------


def _make_user(db: Session, email: str) -> User:
    u = User(
        email=email,
        password_hash=hash_password("password123"),
        full_name=email.split("@")[0],
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def test_expire_soon_targets_only_within_window(
    client: TestClient, db_session
) -> None:
    admin_h = admin_headers(db_session, "exp-admin@example.com")
    plan = _plan(client, admin_h)

    today = date.today()

    # 5 days out: should trigger.
    near_user = _make_user(db_session, "near@example.com")
    _active_membership(
        db_session, user_id=near_user.id, plan_id=plan["id"], end=today + timedelta(days=5)
    )
    # 30 days out: should NOT trigger.
    far_user = _make_user(db_session, "far@example.com")
    _active_membership(
        db_session, user_id=far_user.id, plan_id=plan["id"], end=today + timedelta(days=30)
    )
    # Already past: out of range, should NOT trigger.
    past_user = _make_user(db_session, "past@example.com")
    _active_membership(
        db_session, user_id=past_user.id, plan_id=plan["id"], end=today - timedelta(days=1)
    )

    res = client.post(
        "/api/v1/admin/notifications/expire-soon?days=7", headers=admin_h
    )
    assert res.status_code == 200, res.text
    sent = res.json()["sent"]
    assert sent == 1

    rows = db_session.scalars(
        select(Notification).where(
            Notification.kind == NotificationKind.MEMBERSHIP_EXPIRING,
            Notification.recipient == "near@example.com",
        )
    ).all()
    assert len(rows) == 1
    assert rows[0].status == NotificationStatus.SENT

    # Far + past users got nothing.
    for email in ("far@example.com", "past@example.com"):
        count = len(
            db_session.scalars(
                select(Notification).where(Notification.recipient == email)
            ).all()
        )
        assert count == 0


def test_expire_soon_requires_admin(client: TestClient, db_session) -> None:
    cust = register_customer(client, email="not-admin8@example.com")
    cust_h = {"Authorization": f"Bearer {cust['access_token']}"}
    res = client.post(
        "/api/v1/admin/notifications/expire-soon", headers=cust_h
    )
    assert res.status_code == 403


def test_expire_soon_validates_days(client: TestClient, db_session) -> None:
    admin_h = admin_headers(db_session, "exp-bad-admin@example.com")
    res = client.post(
        "/api/v1/admin/notifications/expire-soon?days=0", headers=admin_h
    )
    assert res.status_code == 422
    res = client.post(
        "/api/v1/admin/notifications/expire-soon?days=999", headers=admin_h
    )
    assert res.status_code == 422


# ------------------------------ /me errors ------------------------------


def test_my_notifications_requires_auth(
    client: TestClient, db_session
) -> None:
    res = client.get("/api/v1/notifications/me")
    # FastAPI returns 403 when there is no auth header (Anonymous with required scope).
    assert res.status_code in (401, 403)
