"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("", summary="Liveness probe")
def liveness() -> dict[str, str]:
    return {"status": "ok"}
