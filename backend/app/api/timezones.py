"""
Timezones API endpoints.
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models.timezone import Timezone
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/timezones", tags=["timezones"])


class TimezoneCreate(BaseModel):
    name: str
    offset: str
    dst_enabled: bool = False
    dst_start: Optional[str] = None
    dst_end: Optional[str] = None


class TimezoneUpdate(BaseModel):
    name: Optional[str] = None
    offset: Optional[str] = None
    dst_enabled: Optional[bool] = None
    dst_start: Optional[str] = None
    dst_end: Optional[str] = None


class TimezoneResponse(BaseModel):
    id: str
    name: str
    offset: str
    dst_enabled: bool
    dst_start: Optional[str]
    dst_end: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[TimezoneResponse])
async def list_timezones(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all timezones."""
    result = await db.execute(select(Timezone).order_by(Timezone.name))
    timezones = result.scalars().all()
    return [
        TimezoneResponse(
            id=str(tz.id),
            name=tz.name,
            offset=tz.offset,
            dst_enabled=tz.dst_enabled,
            dst_start=tz.dst_start,
            dst_end=tz.dst_end,
            created_at=tz.created_at,
        )
        for tz in timezones
    ]


@router.get("/{timezone_id}", response_model=TimezoneResponse)
async def get_timezone(
    timezone_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a timezone by ID."""
    result = await db.execute(
        select(Timezone).where(Timezone.id == uuid.UUID(timezone_id))
    )
    timezone = result.scalar_one_or_none()
    if not timezone:
        raise HTTPException(status_code=404, detail="Timezone not found")
    return TimezoneResponse(
        id=str(timezone.id),
        name=timezone.name,
        offset=timezone.offset,
        dst_enabled=timezone.dst_enabled,
        dst_start=timezone.dst_start,
        dst_end=timezone.dst_end,
        created_at=timezone.created_at,
    )


@router.post("", response_model=TimezoneResponse)
async def create_timezone(
    data: TimezoneCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new timezone."""
    # Check for duplicate name
    existing = await db.execute(select(Timezone).where(Timezone.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Timezone with this name already exists")

    timezone = Timezone(
        name=data.name,
        offset=data.offset,
        dst_enabled=data.dst_enabled,
        dst_start=data.dst_start,
        dst_end=data.dst_end,
    )
    db.add(timezone)
    await db.commit()
    await db.refresh(timezone)

    return TimezoneResponse(
        id=str(timezone.id),
        name=timezone.name,
        offset=timezone.offset,
        dst_enabled=timezone.dst_enabled,
        dst_start=timezone.dst_start,
        dst_end=timezone.dst_end,
        created_at=timezone.created_at,
    )


@router.patch("/{timezone_id}", response_model=TimezoneResponse)
async def update_timezone(
    timezone_id: str,
    data: TimezoneUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a timezone."""
    result = await db.execute(
        select(Timezone).where(Timezone.id == uuid.UUID(timezone_id))
    )
    timezone = result.scalar_one_or_none()
    if not timezone:
        raise HTTPException(status_code=404, detail="Timezone not found")

    # Update fields if provided
    if data.name is not None:
        # Check for duplicate name
        existing = await db.execute(
            select(Timezone).where(Timezone.name == data.name, Timezone.id != timezone.id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Timezone with this name already exists")
        timezone.name = data.name
    if data.offset is not None:
        timezone.offset = data.offset
    if data.dst_enabled is not None:
        timezone.dst_enabled = data.dst_enabled
    if data.dst_start is not None:
        timezone.dst_start = data.dst_start
    if data.dst_end is not None:
        timezone.dst_end = data.dst_end

    await db.commit()
    await db.refresh(timezone)

    return TimezoneResponse(
        id=str(timezone.id),
        name=timezone.name,
        offset=timezone.offset,
        dst_enabled=timezone.dst_enabled,
        dst_start=timezone.dst_start,
        dst_end=timezone.dst_end,
        created_at=timezone.created_at,
    )


@router.delete("/{timezone_id}")
async def delete_timezone(
    timezone_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a timezone."""
    result = await db.execute(
        select(Timezone).where(Timezone.id == uuid.UUID(timezone_id))
    )
    timezone = result.scalar_one_or_none()
    if not timezone:
        raise HTTPException(status_code=404, detail="Timezone not found")

    await db.delete(timezone)
    await db.commit()

    return {"message": "Timezone deleted successfully"}
