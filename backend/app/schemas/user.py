from pydantic import BaseModel, EmailStr
from typing import Optional


class UserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
