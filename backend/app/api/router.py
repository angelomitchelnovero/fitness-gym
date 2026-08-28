"""Top-level API router aggregator."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.endpoints import health

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
