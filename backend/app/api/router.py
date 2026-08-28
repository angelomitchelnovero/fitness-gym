"""Top-level API router aggregator."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.endpoints import (
    admin_dashboard,
    auth,
    checkin,
    customer_dashboard,
    health,
    memberships,
    notifications,
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
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(
    customer_dashboard.router,
    prefix="/dashboard",
    tags=["dashboard"],
)

admin_router = APIRouter()
admin_router.include_router(
    payments.admin_router, prefix="/payments", tags=["admin:payments"]
)
admin_router.include_router(
    checkin.admin_router, prefix="/checkins", tags=["admin:checkins"]
)
admin_router.include_router(admin_dashboard.router, prefix="/dashboard", tags=["admin:dashboard"])
admin_router.include_router(
    notifications.admin_router,
    prefix="/notifications",
    tags=["admin:notifications"],
)
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
