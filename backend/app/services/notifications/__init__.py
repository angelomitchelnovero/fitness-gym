"""Notification channels. Pluggable like payments.

`LoggingChannel` is the default for local development — it just records the
notification row's status without sending anything.
`SmtpChannel` is production-ready and points at the SMTP settings in
`app.core.config` (Mailpit locally).
"""

from app.services.notifications.base import NotificationChannel, NotificationMessage
from app.services.notifications.logging_channel import LoggingChannel as _Logging  # noqa: F401
from app.services.notifications.registry import get_channel

__all__ = ["NotificationChannel", "NotificationMessage", "get_channel"]