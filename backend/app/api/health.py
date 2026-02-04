"""Health monitoring API endpoints."""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.api.deps import get_db, get_current_user
from app.models import Device, DeviceHealthHistory, User
from app.services.health_monitor import HealthMonitorService

router = APIRouter()


@router.get("/devices/{device_id}/history")
async def get_device_health_history(
    device_id: str,
    period: str = Query("7d", regex="^(24h|7d|30d|90d)$"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get health history for a device."""
    # Parse period
    period_map = {"24h": 1, "7d": 7, "30d": 30, "90d": 90}
    days = period_map.get(period, 7)
    since = datetime.utcnow() - timedelta(days=days)

    # Get device
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        return {"error": "Device not found"}

    # Get history
    result = await db.execute(
        select(DeviceHealthHistory)
        .where(
            and_(
                DeviceHealthHistory.device_id == device_id,
                DeviceHealthHistory.timestamp >= since
            )
        )
        .order_by(DeviceHealthHistory.timestamp.asc())
    )
    history = result.scalars().all()

    # Calculate summary
    scores = [h.health_score for h in history]

    return {
        "device_id": device_id,
        "period": period,
        "data_points": [
            {
                "timestamp": h.timestamp.isoformat(),
                "score": h.health_score,
                "sync_success_rate": h.sync_success_rate,
                "avg_response_ms": h.avg_response_ms,
                "alarm_count": h.alarm_count,
                "uptime_seconds": h.uptime_seconds,
            }
            for h in history
        ],
        "summary": {
            "avg_score": int(sum(scores) / len(scores)) if scores else 0,
            "min_score": min(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
            "data_points_count": len(scores),
        }
    }


@router.get("/fleet/summary")
async def get_fleet_health_summary(
    period: str = Query("7d", regex="^(24h|7d|30d)$"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get fleet-wide health summary."""
    # Get all devices with health info
    result = await db.execute(select(Device))
    devices = result.scalars().all()

    # Calculate summary
    by_status = {"healthy": 0, "degraded": 0, "critical": 0, "offline": 0}
    scores = []

    for device in devices:
        status = device.health_status or "healthy"
        by_status[status] = by_status.get(status, 0) + 1
        scores.append(device.health_score or 100)

    # Get worst performers
    worst = sorted(devices, key=lambda d: d.health_score or 100)[:5]

    return {
        "fleet_size": len(devices),
        "fleet_avg_score": int(sum(scores) / len(scores)) if scores else 0,
        "by_status": by_status,
        "worst_performers": [
            {
                "device_id": str(d.id),
                "serial_number": d.serial_number,
                "name": d.name,
                "health_score": d.health_score,
                "health_status": d.health_status,
            }
            for d in worst
        ],
    }


@router.post("/check")
async def trigger_health_check(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Manually trigger a health check."""
    service = HealthMonitorService(db)
    results = await service.check_all_devices()
    return {
        "checked": len(results),
        "status_changes": [r for r in results if r.get("status_changed")],
    }
