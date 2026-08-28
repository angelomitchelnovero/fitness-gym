"""Local no-op channel — captures intent without sending.

The `LoggingChannel` is the default for dev/test: it accepts every message
and reports success without performing any I/O. The notification row is
still recorded in the DB so the rest of the system behaves exactly like
production.
"""

from __future__ import annotations

from app.services.notifications.base import (
    DeliveryResult,
    NotificationChannel,
    NotificationMessage,
)


class LoggingChannel(NotificationChannel):
    name = "logging"

    def send(self, message: NotificationMessage) -> DeliveryResult:
        # Intentionally silent — the notification row in the DB is the record.
        return DeliveryResult(ok=True)