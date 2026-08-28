"""Top-level API router aggregator."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.endpoints import (
    admin_dashboard,
    auth,
    checkin,
    health,
    memberships,
    payments,
    plans,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(plans.router, prefix="/plans", tags=["plans"])
api_router.include_router(memberships.router, prefix="/memberships", tags=["memberships"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(checkin.router, prefix="/checkin", tags=["checkin"])

admin_router = APIRouter()
admin_router.include_router(
    payments.admin_router, prefix="/payments", tags=["admin:payments"]
)
admin_router.include_router(
    checkin.admin_router, prefix="/checkins", tags=["admin:checkins"]
)
admin_router.include_router(admin_dashboard.router, prefix="/dashboard", tags=["admin:dashboard"])
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
