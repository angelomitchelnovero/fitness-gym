"""User / customer schemas."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import UserRole


class UserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    phone: str | None
    role: UserRole
    is_active: bool
    created_at: datetime


class CustomerProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date_of_birth: date | None
    gender: str | None
    address: str | None
    emergency_contact_name: str | None
    emergency_contact_phone: str | None
    notes: str | None


class CustomerDetailResponse(UserSummary):
    profile: CustomerProfileResponse | None = None


class UserListResponse(BaseModel):
    items: list[UserSummary]
    total: int
