"""Provider registry — single source of truth for which providers exist."""

from __future__ import annotations

from app.services.payments.base import PaymentProvider
from app.services.payments.mock import MockPaymentProvider

_REGISTRY: dict[str, type[PaymentProvider]] = {
    MockPaymentProvider.name: MockPaymentProvider,
}


def get_provider(name: str = "mock") -> PaymentProvider:
    cls = _REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"Unknown payment provider: {name!r}")
    return cls()


def register_provider(name: str, cls: type[PaymentProvider]) -> None:
    """Register a new provider. Called at app boot."""
    _REGISTRY[name] = cls