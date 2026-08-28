"""Token/identifier helpers (URL-safe random)."""

from __future__ import annotations

import secrets


def new_qr_token() -> str:
    """Generate a 32-byte URL-safe token for QR check-in."""
    return secrets.token_urlsafe(32)
