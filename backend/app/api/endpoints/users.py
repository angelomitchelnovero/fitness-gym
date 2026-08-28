"""Admin user management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import require_admin
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserListResponse, UserSummary

router = APIRouter()


@router.get(
    "",
    response_model=UserListResponse,
    summary="List users (admin only)",
    dependencies=[Depends(require_admin)],
)
def list_users(
    role: UserRole | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> UserListResponse:
    base = select(User)
    count_q = select(func.count()).select_from(User)
    if role is not None:
        base = base.where(User.role == role)
        count_q = count_q.where(User.role == role)
    total = db.scalar(count_q) or 0
    items = db.scalars(base.order_by(User.created_at.desc()).offset(offset).limit(limit)).all()
    return UserListResponse(
        items=[UserSummary.model_validate(u) for u in items],
        total=total,
    )
