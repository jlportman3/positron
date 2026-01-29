"""
Alarm management API.
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime

from app.api.deps import get_db, get_current_user, require_privilege
from app.models import User, Alarm, Device
from app.schemas.alarm import AlarmResponse, AlarmList, AlarmCounts

router = APIRouter()


@router.get("", response_model=AlarmList)
async def list_alarms(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    device_id: Optional[UUID] = None,
    severity: Optional[str] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List alarms with pagination and filtering."""
    query = select(Alarm)

    if device_id:
        query = query.where(Alarm.device_id == device_id)

    if severity:
        query = query.where(Alarm.severity == severity.upper())

    if active_only:
        query = query.where(Alarm.closing_date == None)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination (most recent first)
    query = query.order_by(Alarm.occurred_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    alarms = result.scalars().all()

    # Get device info for each alarm
    items = []
    for alarm in alarms:
        device_result = await db.execute(
            select(Device).where(Device.id == alarm.device_id)
        )
        device = device_result.scalar_one_or_none()

        items.append(AlarmResponse(
            id=alarm.id,
            device_id=alarm.device_id,
            gam_id=alarm.gam_id,
            if_index=alarm.if_index,
            if_descr=alarm.if_descr,
            cond_type=alarm.cond_type,
            severity=alarm.severity,
            serv_aff=alarm.serv_aff,
            details=alarm.details,
            is_active=alarm.is_active,
            is_critical=alarm.is_critical,
            is_service_affecting=alarm.is_service_affecting,
            occur_time=alarm.occur_time,
            occurred_at=alarm.occurred_at,
            closing_date=alarm.closing_date,
            acknowledged_at=alarm.acknowledged_at,
            acknowledged_by=alarm.acknowledged_by,
            is_manual=alarm.is_manual,
            device_serial=device.serial_number if device else None,
            device_name=device.name if device else None,
        ))

    return AlarmList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/counts", response_model=AlarmCounts)
async def get_alarm_counts(
    device_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get alarm counts by severity (active alarms only)."""
    # Base query for active alarms
    base_filter = Alarm.closing_date == None
    if device_id:
        base_filter = base_filter & (Alarm.device_id == device_id)

    # Count by severity
    critical = await db.scalar(
        select(func.count()).where(base_filter & (Alarm.severity == "CR"))
    )
    major = await db.scalar(
        select(func.count()).where(base_filter & (Alarm.severity == "MJ"))
    )
    minor = await db.scalar(
        select(func.count()).where(base_filter & (Alarm.severity == "MN"))
    )
    normal = await db.scalar(
        select(func.count()).where(base_filter & (Alarm.severity == "NA"))
    )

    return AlarmCounts(
        critical=critical or 0,
        major=major or 0,
        minor=minor or 0,
        normal=normal or 0,
        total=(critical or 0) + (major or 0) + (minor or 0) + (normal or 0),
    )


@router.get("/{alarm_id}", response_model=AlarmResponse)
async def get_alarm(
    alarm_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a single alarm by ID."""
    result = await db.execute(
        select(Alarm).where(Alarm.id == alarm_id)
    )
    alarm = result.scalar_one_or_none()

    if not alarm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alarm not found",
        )

    device_result = await db.execute(
        select(Device).where(Device.id == alarm.device_id)
    )
    device = device_result.scalar_one_or_none()

    return AlarmResponse(
        id=alarm.id,
        device_id=alarm.device_id,
        gam_id=alarm.gam_id,
        if_index=alarm.if_index,
        if_descr=alarm.if_descr,
        cond_type=alarm.cond_type,
        severity=alarm.severity,
        serv_aff=alarm.serv_aff,
        details=alarm.details,
        is_active=alarm.is_active,
        is_critical=alarm.is_critical,
        is_service_affecting=alarm.is_service_affecting,
        occur_time=alarm.occur_time,
        occurred_at=alarm.occurred_at,
        closing_date=alarm.closing_date,
        acknowledged_at=alarm.acknowledged_at,
        acknowledged_by=alarm.acknowledged_by,
        is_manual=alarm.is_manual,
        device_serial=device.serial_number if device else None,
        device_name=device.name if device else None,
    )


@router.post("/{alarm_id}/acknowledge")
async def acknowledge_alarm(
    alarm_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(3)),  # Operator level
):
    """Acknowledge an alarm."""
    result = await db.execute(
        select(Alarm).where(Alarm.id == alarm_id)
    )
    alarm = result.scalar_one_or_none()

    if not alarm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alarm not found",
        )

    if alarm.acknowledged_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alarm already acknowledged",
        )

    alarm.acknowledged_at = datetime.utcnow()
    alarm.acknowledged_by = user.username
    await db.commit()

    return {"message": "Alarm acknowledged", "acknowledged_by": user.username}


@router.post("/{alarm_id}/close")
async def close_alarm(
    alarm_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(5)),  # Manager level
):
    """Manually close an alarm."""
    result = await db.execute(
        select(Alarm).where(Alarm.id == alarm_id)
    )
    alarm = result.scalar_one_or_none()

    if not alarm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alarm not found",
        )

    if alarm.closing_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alarm already closed",
        )

    alarm.closing_date = datetime.utcnow()
    alarm.is_manual = True
    await db.commit()

    return {"message": "Alarm closed manually"}
