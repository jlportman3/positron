"""
User management API endpoints.
"""
import logging
import uuid as uuid_mod
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.security import hash_password, PRIVILEGE_LEVELS
from app.api.deps import get_db, get_current_user, require_privilege
from app.models import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserList
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


def _user_response(u: User) -> UserResponse:
    return UserResponse(
        id=u.id,
        username=u.username,
        email=u.email,
        enabled=u.enabled,
        is_device=u.is_device,
        is_radius=u.is_radius,
        privilege_level=u.privilege_level,
        privilege_name=PRIVILEGE_LEVELS.get(u.privilege_level, "Unknown"),
        session_timeout=u.session_timeout,
        timezone=u.timezone,
        last_activity=u.last_activity,
        last_login=u.last_login,
        invitation_pending=bool(u.invitation_token),
        created_at=u.created_at,
        updated_at=u.updated_at,
    )

router = APIRouter()


@router.get("", response_model=UserList)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    search: Optional[str] = None,
    enabled: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(7)),  # Admin level
):
    """List all users with pagination."""
    query = select(User)

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (User.username.ilike(search_pattern)) |
            (User.email.ilike(search_pattern))
        )

    if enabled is not None:
        query = query.where(User.enabled == enabled)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    query = query.order_by(User.username)
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    users = result.scalars().all()

    items = [_user_response(u) for u in users]

    return UserList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user: User = Depends(get_current_user),
):
    """Get current user's information."""
    return _user_response(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_privilege(7)),  # Admin level
):
    """Get a user by ID."""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return _user_response(user)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_privilege(7)),  # Admin level
):
    """Create a new user."""
    # Check for duplicate username
    existing = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    # Check for duplicate email
    if user_data.email:
        existing_email = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        if existing_email.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists",
            )

    # Cannot create user with higher privilege than current user
    if user_data.privilege_level > current_user.privilege_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create user with higher privilege level",
        )

    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        enabled=user_data.enabled,
        privilege_level=user_data.privilege_level,
        session_timeout=user_data.session_timeout,
        timezone=user_data.timezone,
        created_by=current_user.username,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return _user_response(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_privilege(7)),  # Admin level
):
    """Update a user."""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Cannot modify user with higher or equal privilege (unless self)
    if user.id != current_user.id and user.privilege_level >= current_user.privilege_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify user with equal or higher privilege",
        )

    # Cannot elevate privilege above own level
    if user_data.privilege_level and user_data.privilege_level > current_user.privilege_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot set privilege level higher than your own",
        )

    # Update fields
    update_data = user_data.model_dump(exclude_unset=True)

    # Hash password if provided
    if "password" in update_data:
        update_data["password_hash"] = hash_password(update_data.pop("password"))

    for field, value in update_data.items():
        setattr(user, field, value)

    user.updated_by = current_user.username
    await db.commit()
    await db.refresh(user)

    return _user_response(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_privilege(9)),  # SuperAdmin level
):
    """Delete a user."""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Cannot delete self
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete yourself",
        )

    # Cannot delete user with higher or equal privilege
    if user.privilege_level >= current_user.privilege_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete user with equal or higher privilege",
        )

    await db.delete(user)
    await db.commit()


class InviteUserRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    email: EmailStr
    privilege_level: int = Field(5, ge=0, le=15)
    session_timeout: int = Field(30, ge=1, le=1440)


@router.post("/invite", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def invite_user(
    data: InviteUserRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_privilege(7)),
):
    """Invite a new user via email. Creates a disabled account with an invitation token."""
    # Check duplicate username
    existing = await db.execute(select(User).where(User.username == data.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username already exists")

    # Check duplicate email
    existing_email = await db.execute(select(User).where(User.email == data.email))
    if existing_email.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already exists")

    if data.privilege_level > current_user.privilege_level:
        raise HTTPException(status_code=403, detail="Cannot invite user with higher privilege level")

    token = uuid_mod.uuid4().hex
    expires = datetime.utcnow() + timedelta(hours=72)

    user = User(
        username=data.username,
        email=data.email,
        password_hash="!invited",  # unusable hash
        enabled=False,
        privilege_level=data.privilege_level,
        session_timeout=data.session_timeout,
        invitation_token=token,
        invitation_expires=expires,
        created_by=current_user.username,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Build invite URL from request origin
    origin = request.headers.get("origin", "")
    if not origin:
        origin = f"{request.url.scheme}://{request.url.hostname}"
        if request.url.port and request.url.port not in (80, 443):
            origin += f":{request.url.port}"
    invite_url = f"{origin}/accept-invite?token={token}"

    # Send invitation email
    try:
        ns = NotificationService(db)
        await ns.send_email(
            to=data.email,
            subject="Alamo GAM - You've been invited",
            body=f"You have been invited to Alamo GAM by {current_user.username}.\n\nClick the link below to set your password and activate your account:\n\n{invite_url}\n\nThis link expires in 72 hours.",
            html_body=f"""
<h2>Alamo GAM Invitation</h2>
<p>You have been invited to Alamo GAM by <strong>{current_user.username}</strong>.</p>
<p>Click the link below to set your password and activate your account:</p>
<p><a href="{invite_url}" style="display:inline-block;padding:10px 20px;background:#51bcda;color:white;text-decoration:none;border-radius:4px;">Accept Invitation</a></p>
<p style="color:#999;font-size:12px;">This link expires in 72 hours. If the button doesn't work, copy this URL: {invite_url}</p>
""",
        )
    except Exception as e:
        logger.error(f"Failed to send invitation email to {data.email}: {e}")
        # Don't fail the creation, just warn
        pass

    return _user_response(user)


@router.post("/{user_id}/resend-invite")
async def resend_invite(
    user_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_privilege(7)),
):
    """Resend invitation email for a pending user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.enabled:
        raise HTTPException(status_code=400, detail="User is already active")

    if not user.email:
        raise HTTPException(status_code=400, detail="User has no email address")

    # Regenerate token
    token = uuid_mod.uuid4().hex
    user.invitation_token = token
    user.invitation_expires = datetime.utcnow() + timedelta(hours=72)
    await db.commit()

    origin = request.headers.get("origin", "")
    if not origin:
        origin = f"{request.url.scheme}://{request.url.hostname}"
        if request.url.port and request.url.port not in (80, 443):
            origin += f":{request.url.port}"
    invite_url = f"{origin}/accept-invite?token={token}"

    try:
        ns = NotificationService(db)
        await ns.send_email(
            to=user.email,
            subject="Alamo GAM - Invitation Reminder",
            body=f"You have been invited to Alamo GAM.\n\nClick the link below to set your password:\n\n{invite_url}\n\nThis link expires in 72 hours.",
            html_body=f"""
<h2>Alamo GAM Invitation</h2>
<p>This is a reminder that you have been invited to Alamo GAM.</p>
<p><a href="{invite_url}" style="display:inline-block;padding:10px 20px;background:#51bcda;color:white;text-decoration:none;border-radius:4px;">Accept Invitation</a></p>
<p style="color:#999;font-size:12px;">This link expires in 72 hours.</p>
""",
        )
        return {"message": f"Invitation resent to {user.email}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e}")
