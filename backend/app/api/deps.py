"""
API dependencies for authentication and authorization.
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status, Request, Header
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import async_session_maker
from app.core.config import settings
from app.core.security import (
    verify_password,
    is_session_expired,
    has_permission,
    decode_basic_auth,
)
from app.models import User, Session
from app.models.setting import Setting

# HTTP Basic auth for device announcements
basic_security = HTTPBasic(auto_error=False)


async def get_db():
    """Get database session."""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def get_current_session(
    request: Request,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> Session:
    """Get current user session from cookie or header.

    Raises HTTPException if not authenticated.
    """
    session_id = None

    # Try cookie first
    session_id = request.cookies.get("session_id")

    # Fall back to Authorization header (Bearer token)
    if not session_id and authorization:
        if authorization.startswith("Bearer "):
            session_id = authorization[7:]

    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    # Look up session
    result = await db.execute(
        select(Session).where(Session.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session",
        )

    # Check expiration
    if is_session_expired(session.last_activity, session.expires_at):
        await db.delete(session)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired",
        )

    # Update last activity
    session.last_activity = datetime.utcnow()
    session.ip_address = request.client.host if request.client else None
    await db.commit()

    return session


async def get_current_user(
    session: Session = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current authenticated user.

    Raises HTTPException if not authenticated.
    """
    result = await db.execute(
        select(User).where(User.id == session.user_id)
    )
    user = result.scalar_one_or_none()

    if not user or not user.enabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled",
        )

    return user


async def verify_device_auth(
    credentials: Optional[HTTPBasicCredentials] = Depends(basic_security),
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> bool:
    """Verify device Basic Auth for announcements.

    Validates against the users table.
    Returns True if valid credentials or if auth is optional and none provided.
    """
    username = None
    password = None

    # Try HTTPBasic first
    if credentials:
        username = credentials.username
        password = credentials.password
    # Fall back to manual header parsing
    elif authorization:
        try:
            username, password = decode_basic_auth(authorization)
        except ValueError:
            pass

    if not username or not password:
        if settings.device_auth_optional:
            return True  # Auth is optional, allow through
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Device authentication required",
            headers={"WWW-Authenticate": "Basic"},
        )

    # Validate against users table ('device' user with privilege level 1)
    result = await db.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()

    if not user or not user.enabled or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid device credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return True


def require_privilege(min_level: int):
    """Dependency factory to require minimum privilege level."""

    async def check_privilege(user: User = Depends(get_current_user)):
        if not has_permission(user.privilege_level, min_level):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient privileges. Required level: {min_level}",
            )
        return user

    return check_privilege


def require_permission(key: str, default_level: int = 3):
    """Dependency factory that reads the required privilege level from a DB setting.

    Looks up setting key 'permission_{key}' for the required level.
    Falls back to default_level if not configured.
    """

    async def check_permission(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        result = await db.execute(
            select(Setting).where(Setting.key == f"permission_{key}")
        )
        setting = result.scalar_one_or_none()
        min_level = default_level
        if setting and setting.value:
            try:
                min_level = int(setting.value)
            except ValueError:
                pass

        if not has_permission(user.privilege_level, min_level):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient privileges for '{key}'. Required level: {min_level}",
            )
        return user

    return check_permission
