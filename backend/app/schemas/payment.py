"""Schemas for payments."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CheckoutRequest(BaseModel):
    membership_id: int = Field(ge=1)
    provider: str = Field(default="mock", max_length=40)
    method: str | None = Field(default=None, max_length=40)


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    membership_id: int | None
    amount_cents: int
    currency: str
    provider: str
    external_id: str | None
    status: str
    method: str | None
    failure_reason: str | None
    paid_at: datetime | None
    created_at: datetime


class PaymentListResponse(BaseModel):
    items: list[PaymentRead]
    total: int


class CheckoutResponse(BaseModel):
    payment: PaymentRead
    checkout_url: str | None = None  # mock provider leaves this None


class VerifyRequest(BaseModel):
    """Optional dev-only override for the mock provider.

    In production, /verify simply asks the provider. The mock provider lets
    tests force a failure.
    """

    force_outcome: str | None = Field(default=None, pattern="^(succeeded|failed)$")