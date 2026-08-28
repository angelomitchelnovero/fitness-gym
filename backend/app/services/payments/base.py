"""Abstract payment provider interface."""

from __future__ import annotations

import abc
from dataclasses import dataclass


@dataclass(frozen=True)
class CheckoutInput:
    """Inputs for creating a checkout with a provider."""

    amount_cents: int
    currency: str
    description: str
    user_id: int
    membership_id: int | None = None
    method: str | None = None  # e.g. "card", "gcash", "maya"


@dataclass(frozen=True)
class CheckoutResult:
    """Provider's response after creating a checkout."""

    external_id: str  # provider-side identifier
    status: str       # one of PaymentStatus values
    method: str | None = None
    raw: dict | None = None  # for debugging, never trust client data from here


@dataclass(frozen=True)
class VerificationResult:
    """Provider's response after verifying a checkout/charge."""

    external_id: str
    status: str
    paid_at: str | None = None  # ISO 8601 timestamp from the provider
    failure_reason: str | None = None
    raw: dict | None = None


class PaymentProvider(abc.ABC):
    """Pluggable payment provider interface."""

    name: str

    @abc.abstractmethod
    def create_checkout(self, payload: CheckoutInput) -> CheckoutResult:
        """Initiate a charge. Returns a provider-side reference id."""

    @abc.abstractmethod
    def verify(self, external_id: str) -> VerificationResult:
        """Re-check the charge with the provider.

        The backend NEVER trusts a "payment success" signal from the frontend;
        success is only confirmed by talking to the provider here.
        """

    def cancel(self, external_id: str) -> VerificationResult:  # noqa: D401
        """Cancel a pending checkout. Default implementation is a no-op."""
        return VerificationResult(external_id=external_id, status="cancelled")