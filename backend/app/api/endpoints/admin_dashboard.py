"""Admin dashboard summary endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.admin_dashboard import DashboardSummary
from app.services import admin_service

router = APIRouter()


@router.get(
    "",
    response_model=DashboardSummary,
    summary="[admin] Dashboard summary (totals + recent activity)",
)
def dashboard(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> DashboardSummary:
    return DashboardSummary.model_validate(admin_service.build_dashboard(db))