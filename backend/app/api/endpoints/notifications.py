"""Notification endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.notification import (
    NotificationListResponse,
    NotificationRead,
    TriggerExpiryResponse,
)
from app.services import notification_service

router = APIRouter()


@router.get(
    "/me",
    response_model=NotificationListResponse,
    summary="List my notifications (inbox)",
)
def my_notifications(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> NotificationListResponse:
    items = notification_service.list_for_user(db, user)
    return NotificationListResponse(
        items=[NotificationRead.model_validate(n) for n in items],
        total=len(items),
    )


admin_router = APIRouter()


@admin_router.post(
    "/expire-soon",
    response_model=TriggerExpiryResponse,
    summary="[admin] Enqueue expiry reminders for memberships ending soon",
)
def trigger_expiry(
    days: int | None = Query(default=None, ge=1, le=90),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> TriggerExpiryResponse:
    sent = notification_service.send_expiry_reminders(db, days=days)
    return TriggerExpiryResponse(sent=sent)