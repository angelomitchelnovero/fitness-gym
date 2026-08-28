"""Top-level API router aggregator."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.endpoints import auth, checkin, health, memberships, payments, plans, users

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(plans.router, prefix="/plans", tags=["plans"])
api_router.include_router(memberships.router, prefix="/memberships", tags=["memberships"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(
    payments.admin_router,
    prefix="/admin/payments",
    tags=["admin:payments"],
)
api_router.include_router(checkin.router, prefix="/checkin", tags=["checkin"])
api_router.include_router(
    checkin.admin_router,
    prefix="/admin/checkins",
    tags=["admin:checkins"],
)
