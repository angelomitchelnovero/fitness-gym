"""Abstract notification channel interface."""

from __future__ import annotations

import abc
from dataclasses import dataclass


@dataclass(frozen=True)
class NotificationMessage:
    """Outbound message envelope — channel-agnostic."""

    recipient: str
    subject: str
    body: str
    kind: str = ""


@dataclass(frozen=True)
class DeliveryResult:
    """Result of a single send attempt."""

    ok: bool
    error: str | None = None


class NotificationChannel(abc.ABC):
    """Pluggable transport for outbound notifications."""

    name: str

    @abc.abstractmethod
    def send(self, message: NotificationMessage) -> DeliveryResult:
        """Deliver the message. Returns ok=True on success."""