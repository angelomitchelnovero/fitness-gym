"""Admin user management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import require_admin
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserListResponse, UserSummary, UserUpdate
from app.services import user_service

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


@router.post(
    "",
    response_model=UserSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user manually (admin only)",
    dependencies=[Depends(require_admin)],
)
def create_user(
    email: str = Body(...),
    full_name: str = Body(...),
    phone: str | None = Body(None),
    password: str | None = Body(None),
    db: Session = Depends(get_db),
) -> UserSummary:
    try:
        user = user_service.admin_create_user(db, email, full_name, phone, password)
        return UserSummary.model_validate(user)
    except user_service.EmailAlreadyTakenError as exc:
        raise HTTPException(status_code=400, detail=f"Email {exc} is already taken")


@router.patch(
    "/{user_id}",
    response_model=UserSummary,
    summary="Update a user (admin only)",
    dependencies=[Depends(require_admin)],
)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
) -> UserSummary:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    updated = user_service.admin_update_user(db, user, payload.model_dump(exclude_unset=True))
    return UserSummary.model_validate(updated)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user (admin only)",
    dependencies=[Depends(require_admin)],
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
) -> None:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user_service.admin_delete_user(db, user)
