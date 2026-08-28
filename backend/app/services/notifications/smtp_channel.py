"""SMTP-backed channel. Sends real emails via `SMTP_HOST`.

In local dev, Mailpit captures everything at SMTP_HOST:SMTP_PORT so emails
never leave the box. Production uses the same code path with real SMTP
credentials.
"""

from __future__ import annotations

import smtplib
from email.message import EmailMessage as StdEmailMessage

from app.core.config import settings
from app.services.notifications.base import (
    DeliveryResult,
    NotificationChannel,
    NotificationMessage,
)


class SmtpChannel(NotificationChannel):
    name = "smtp"

    def send(self, message: NotificationMessage) -> DeliveryResult:
        msg = StdEmailMessage()
        msg["Subject"] = message.subject
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg["To"] = message.recipient
        msg.set_content(message.body)
        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as s:
                s.send_message(msg)
            return DeliveryResult(ok=True)
        except Exception as exc:  # noqa: BLE001
            return DeliveryResult(ok=False, error=str(exc))