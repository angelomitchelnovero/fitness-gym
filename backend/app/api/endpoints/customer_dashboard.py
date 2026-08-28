"""Customer dashboard endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.customer_dashboard import CustomerDashboard
from app.services import dashboard_service

router = APIRouter()


@router.get(
    "/me",
    response_model=CustomerDashboard,
    summary="Summary view for the current user's dashboard",
)
def my_dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CustomerDashboard:
    return CustomerDashboard.model_validate(
        dashboard_service.build_customer_dashboard(db, user)
    )