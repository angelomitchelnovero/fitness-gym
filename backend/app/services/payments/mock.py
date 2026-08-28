"""Local mock payment provider for development.

The mock provider creates a checkout with a known external_id pattern so
verification can be deterministic during local testing:

    pi_mock_<random>

Verification accepts any external_id; a separate endpoint accepts a
"force_succeed" / "force_fail" flag from the test client only. In real use,
verification would talk to the provider's API; here we just trust whatever
the dev set last.

This provider never takes input from the frontend for whether payment
"actually" succeeded — only the backend (during the verify call) can decide.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime

from app.models.payment import PaymentStatus
from app.services.payments.base import (
    CheckoutInput,
    CheckoutResult,
    PaymentProvider,
    VerificationResult,
)


class MockPaymentProvider(PaymentProvider):
    name = "mock"

    # In-memory record of the last forced outcome. Production would not need this.
    _forced_outcome: dict[str, str] = {}

    def create_checkout(self, payload: CheckoutInput) -> CheckoutResult:
        external_id = f"pi_mock_{secrets.token_urlsafe(8)}"
        # Default to pending; admin/dev can flip via /payments/{id}/verify.
        self._forced_outcome[external_id] = PaymentStatus.SUCCEEDED
        return CheckoutResult(
            external_id=external_id,
            status=PaymentStatus.PENDING,
            method=payload.method or "mock_card",
        )

    def verify(self, external_id: str) -> VerificationResult:
        outcome = self._forced_outcome.get(external_id, PaymentStatus.SUCCEEDED)
        now = datetime.now(UTC).isoformat() if outcome == PaymentStatus.SUCCEEDED else None
        return VerificationResult(
            external_id=external_id,
            status=outcome,
            paid_at=now,
            failure_reason=None if outcome == PaymentStatus.SUCCEEDED else "Mock failure",
        )

    @classmethod
    def force_outcome(cls, external_id: str, status: str) -> None:
        cls._forced_outcome[external_id] = status