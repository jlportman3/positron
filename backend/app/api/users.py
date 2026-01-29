"""
User management API endpoints.
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.security import hash_password, PRIVILEGE_LEVELS
from app.api.deps import get_db, get_current_user, require_privilege
from app.models import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserList

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

    items = [
        UserResponse(
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
            created_at=u.created_at,
            updated_at=u.updated_at,
        )
        for u in users
    ]

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
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        enabled=user.enabled,
        is_device=user.is_device,
        is_radius=user.is_radius,
        privilege_level=user.privilege_level,
        privilege_name=PRIVILEGE_LEVELS.get(user.privilege_level, "Unknown"),
        session_timeout=user.session_timeout,
        timezone=user.timezone,
        last_activity=user.last_activity,
        last_login=user.last_login,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


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

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        enabled=user.enabled,
        is_device=user.is_device,
        is_radius=user.is_radius,
        privilege_level=user.privilege_level,
        privilege_name=PRIVILEGE_LEVELS.get(user.privilege_level, "Unknown"),
        session_timeout=user.session_timeout,
        timezone=user.timezone,
        last_activity=user.last_activity,
        last_login=user.last_login,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


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

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        enabled=user.enabled,
        is_device=user.is_device,
        is_radius=user.is_radius,
        privilege_level=user.privilege_level,
        privilege_name=PRIVILEGE_LEVELS.get(user.privilege_level, "Unknown"),
        session_timeout=user.session_timeout,
        timezone=user.timezone,
        last_activity=user.last_activity,
        last_login=user.last_login,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


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

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        enabled=user.enabled,
        is_device=user.is_device,
        is_radius=user.is_radius,
        privilege_level=user.privilege_level,
        privilege_name=PRIVILEGE_LEVELS.get(user.privilege_level, "Unknown"),
        session_timeout=user.session_timeout,
        timezone=user.timezone,
        last_activity=user.last_activity,
        last_login=user.last_login,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


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
