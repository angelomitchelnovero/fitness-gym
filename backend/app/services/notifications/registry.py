"""Provider registry — single source of truth for which channels exist."""

from __future__ import annotations

from app.services.notifications.base import NotificationChannel
from app.services.notifications.logging_channel import LoggingChannel
from app.services.notifications.smtp_channel import SmtpChannel

_REGISTRY: dict[str, type[NotificationChannel]] = {
    LoggingChannel.name: LoggingChannel,
    SmtpChannel.name: SmtpChannel,
}


def get_channel(name: str) -> NotificationChannel:
    cls = _REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"Unknown notification channel: {name!r}")
    return cls()


def register_channel(name: str, cls: type[NotificationChannel]) -> None:
    """Register a new channel. Called at app boot."""
    _REGISTRY[name] = cls