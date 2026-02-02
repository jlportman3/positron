"""
User schemas.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from uuid import UUID


class UserBase(BaseModel):
    """Base user fields."""
    username: str = Field(..., min_length=1, max_length=64)
    email: Optional[EmailStr] = None
    enabled: bool = True
    privilege_level: int = Field(1, ge=0, le=15)
    session_timeout: int = Field(30, ge=1, le=1440)  # 1 min to 24 hours
    timezone: Optional[str] = None


class UserCreate(UserBase):
    """User creation request."""
    password: str = Field(..., min_length=4)


class UserUpdate(BaseModel):
    """User update request (all fields optional)."""
    username: Optional[str] = Field(None, min_length=1, max_length=64)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=4)
    enabled: Optional[bool] = None
    privilege_level: Optional[int] = Field(None, ge=0, le=15)
    session_timeout: Optional[int] = Field(None, ge=1, le=1440)
    timezone: Optional[str] = None


class UserResponse(BaseModel):
    """User response."""
    id: UUID
    username: str
    email: Optional[str] = None
    enabled: bool
    is_device: bool
    is_radius: bool = False
    privilege_level: int
    privilege_name: str
    session_timeout: int
    timezone: Optional[str] = None
    last_activity: Optional[datetime] = None
    last_login: Optional[datetime] = None
    invitation_pending: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserList(BaseModel):
    """Paginated user list."""
    items: List[UserResponse]
    total: int
    page: int
    page_size: int
