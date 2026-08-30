"""Schemas for check-in / membership card."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CardResponse(BaseModel):
    """Issued membership card / QR payload."""

    token: str
    membership_id: int
    user_id: int
    plan_name: str
    issued_at: datetime
    expires_at: datetime


class ScanRequest(BaseModel):
    """Scanner submits the raw QR string."""

    token: str = Field(min_length=1, max_length=4096)
    source: str = Field(default="qr", pattern="^(qr|manual)$")


class ScanOutcome(BaseModel):
    """What the scanner did — recorded whether the person was admitted or not."""

    accepted: bool
    reason: str | None = None
    user_id: int | None = None
    membership_id: int | None = None
    scanned_at: datetime
    check_in_id: int


class CheckInRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    membership_id: int | None
    scanned_at: datetime
    source: str
    accepted: bool
    reason: str | None


class CheckInListResponse(BaseModel):
    items: list[CheckInRead]
    total: int