"""Schemas for the notifications inbox + admin triggers."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    channel: str
    kind: str
    subject: str
    body: str
    recipient: str
    status: str
    sent_at: datetime | None
    error: str | None
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationRead]
    total: int


class TriggerExpiryResponse(BaseModel):
    sent: int