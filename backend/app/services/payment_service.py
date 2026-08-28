"""Payment service — orchestrates providers and the membership activation hook.

Domain exceptions raised here:
  PaymentNotFoundError, MembershipNotFoundError, NotOwnerError,
  NotPayableError, BadReferenceError

The endpoint layer translates these into HTTP responses.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.membership import Membership, MembershipStatus
from app.models.payment import Payment, PaymentStatus
from app.models.user import User
from app.services.membership_service import _compute_status
from app.services.payments.base import CheckoutInput, PaymentProvider


class PaymentNotFoundError(Exception):
    pass


class MembershipNotFoundError(Exception):
    pass


class NotOwnerError(Exception):
    pass


class NotPayableError(Exception):
    pass


class BadReferenceError(Exception):
    pass


def _activate_membership(db: Session, payment: Payment) -> None:
    membership = db.scalar(
        select(Membership).where(Membership.id == payment.membership_id)
    )
    if membership is None:
        return
    now = datetime.now(UTC)
    # Order matters: _compute_status checks `activated_at is None` to decide
    # if the membership is still pending. Set it first.
    membership.activated_at = now
    membership.status = _compute_status(membership)
    # Link the membership to its payment (post_update handles the cycle).
    membership.payment_id = payment.id
    db.flush()


class PaymentService:
    """High-level payment orchestration.

    This is the only place where `Membership.status` flips to ACTIVE — the
    provider itself never activates memberships.
    """

    def start_payment(
        self,
        db: Session,
        *,
        user: User,
        membership_id: int,
        provider: PaymentProvider,
        method: str | None = None,
    ) -> Payment:
        """Create a checkout with the provider and persist a PENDING payment.

        Returns the persisted Payment row.
        """
        membership = db.scalar(
            select(Membership).where(Membership.id == membership_id)
        )
        if membership is None:
            raise MembershipNotFoundError(str(membership_id))
        if membership.user_id != user.id:
            raise NotOwnerError("Cannot pay for another user's membership")
        if membership.status not in (MembershipStatus.PENDING, MembershipStatus.EXPIRED):
            raise NotPayableError(
                "Only pending or expired memberships can be paid for",
            )

        # Snapshot price so admin edits don't change what an existing member pays.
        amount_cents = membership.price_cents
        currency = membership.currency
        plan_name = membership.plan.name if membership.plan else "plan"

        result = provider.create_checkout(
            CheckoutInput(
                amount_cents=amount_cents,
                currency=currency,
                description=f"Membership #{membership.id} ({plan_name})",
                user_id=user.id,
                membership_id=membership.id,
                method=method,
            )
        )

        payment = Payment(
            user_id=user.id,
            membership_id=membership.id,
            amount_cents=amount_cents,
            currency=currency,
            provider=provider.name,
            external_id=result.external_id,
            status=result.status or PaymentStatus.PENDING,
            method=result.method or method,
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment

    def verify_payment(
        self,
        db: Session,
        *,
        user: User,
        payment_id: int,
        provider: PaymentProvider,
        force_outcome: str | None = None,
    ) -> Payment:
        """Verify a payment with the provider and activate on success."""
        payment = db.get(Payment, payment_id)
        if payment is None:
            raise PaymentNotFoundError(str(payment_id))
        if payment.user_id != user.id:
            raise NotOwnerError("Cannot verify another user's payment")
        if payment.status in (PaymentStatus.SUCCEEDED, PaymentStatus.REFUNDED):
            return payment  # already terminal

        # Mock provider hook for tests / local dev.
        if force_outcome is not None and provider.name == "mock":
            from app.services.payments.mock import MockPaymentProvider
            MockPaymentProvider.force_outcome(payment.external_id or "", force_outcome)

        if not payment.external_id:
            raise BadReferenceError("Payment has no provider reference id")

        result = provider.verify(payment.external_id)

        payment.status = result.status
        payment.failure_reason = result.failure_reason
        if result.paid_at:
            try:
                payment.paid_at = datetime.fromisoformat(result.paid_at)
            except ValueError:
                payment.paid_at = datetime.now(UTC)
        else:
            payment.paid_at = None
        db.flush()

        if result.status == PaymentStatus.SUCCEEDED:
            _activate_membership(db, payment)

        db.commit()
        db.refresh(payment)

        # Fire-and-forget notification. Imports here avoid a circular dep
        # between payment_service and notification_service.
        if payment.status == PaymentStatus.SUCCEEDED:
            try:
                from app.services import notification_service
                notification_service.trigger_payment_receipt(db, payment, user)
            except Exception as exc:  # noqa: BLE001
                # Never let a notification failure block a successful payment.
                import logging
                logging.getLogger(__name__).warning(
                    "notification failed for payment %s: %s", payment.id, exc,
                )

        return payment

    def list_for_user(self, db: Session, user: User) -> list[Payment]:
        return list(
            db.scalars(
                select(Payment)
                .where(Payment.user_id == user.id)
                .order_by(Payment.created_at.desc())
            )
        )

    def list_all(self, db: Session) -> list[Payment]:
        return list(
            db.scalars(select(Payment).order_by(Payment.created_at.desc()))
        )


payment_service = PaymentService()