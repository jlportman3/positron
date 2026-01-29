"""
Authentication schemas.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID


class LoginRequest(BaseModel):
    """Login request with username and password."""
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """Login response with session info."""
    session_id: str
    username: str
    privilege_level: int
    privilege_name: str
    expires_at: datetime
    login_banner: Optional[str] = None
    require_terms_acceptance: bool = False


class SessionInfo(BaseModel):
    """Current session information."""
    session_id: str
    user_id: UUID
    username: str
    privilege_level: int
    privilege_name: str
    ip_address: Optional[str] = None
    created_at: datetime
    last_activity: datetime
    expires_at: datetime

    class Config:
        from_attributes = True
