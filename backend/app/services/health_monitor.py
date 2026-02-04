"""
Health monitoring service for device fleet.

Computes health scores based on:
- Sync success rate (40 points)
- Response time (25 points)
- Active alarms (20 points)
- Uptime (15 points)
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models import Device, SyncAttempt, Alarm, DeviceHealthHistory

logger = logging.getLogger(__name__)

# Health status thresholds
HEALTHY_THRESHOLD = 80
DEGRADED_THRESHOLD = 60
CRITICAL_THRESHOLD = 30


def get_status_from_score(score: int, is_online: bool) -> str:
    """Determine health status from score."""
    if not is_online:
        return "offline"
    if score >= HEALTHY_THRESHOLD:
        return "healthy"
    if score >= DEGRADED_THRESHOLD:
        return "degraded"
    if score >= CRITICAL_THRESHOLD:
        return "critical"
    return "offline"


class HealthMonitorService:
    """Service for monitoring device health."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_sync_success_rate(self, device_id: str, hours: int = 24) -> float:
        """Calculate sync success rate over the given period."""
        since = datetime.utcnow() - timedelta(hours=hours)

        result = await self.db.execute(
            select(
                func.count().filter(SyncAttempt.success == True).label("success_count"),
                func.count().label("total_count")
            ).where(
                and_(
                    SyncAttempt.device_id == device_id,
                    SyncAttempt.timestamp >= since
                )
            )
        )
        row = result.one()

        if row.total_count == 0:
            return 1.0  # No attempts = assume healthy

        return row.success_count / row.total_count

    async def get_avg_response_time(self, device_id: str, hours: int = 24) -> int:
        """Calculate average response time in ms over the given period."""
        since = datetime.utcnow() - timedelta(hours=hours)

        result = await self.db.execute(
            select(func.avg(SyncAttempt.duration_ms)).where(
                and_(
                    SyncAttempt.device_id == device_id,
                    SyncAttempt.timestamp >= since,
                    SyncAttempt.success == True
                )
            )
        )
        avg = result.scalar()

        return int(avg) if avg else 0

    async def get_active_alarm_count(self, device_id: str) -> int:
        """Count active alarms for device."""
        result = await self.db.execute(
            select(func.count()).where(
                and_(
                    Alarm.device_id == device_id,
                    Alarm.closing_date == None
                )
            )
        )
        return result.scalar() or 0

    def calculate_response_time_score(self, avg_ms: int) -> float:
        """Calculate response time score (0-100)."""
        if avg_ms <= 500:
            return 100.0
        if avg_ms >= 5000:
            return 0.0
        # Linear scale from 500ms (100) to 5000ms (0)
        return 100.0 * (5000 - avg_ms) / 4500

    def calculate_alarm_score(self, alarm_count: int) -> float:
        """Calculate alarm score (0-100)."""
        score = 100 - (alarm_count * 10)
        return max(0.0, score)

    def calculate_uptime_score(self, device: Device) -> float:
        """Calculate uptime score based on device uptime."""
        if not device.uptime:
            return 100.0  # No uptime data = assume healthy

        # Expected uptime is 24 hours in seconds
        expected_seconds = 24 * 60 * 60
        actual_seconds = min(device.uptime, expected_seconds)

        return 100.0 * actual_seconds / expected_seconds

    async def compute_health_score(self, device: Device) -> Tuple[int, dict]:
        """
        Compute health score for a device.

        Returns:
            Tuple of (score, factors dict)
        """
        # Get metrics
        sync_rate = await self.get_sync_success_rate(str(device.id))
        avg_response = await self.get_avg_response_time(str(device.id))
        alarm_count = await self.get_active_alarm_count(str(device.id))

        # Calculate component scores
        sync_score = sync_rate * 40
        response_score = self.calculate_response_time_score(avg_response) * 0.25
        alarm_score = self.calculate_alarm_score(alarm_count) * 0.20
        uptime_score = self.calculate_uptime_score(device) * 0.15

        # Total score
        total = int(sync_score + response_score + alarm_score + uptime_score)
        total = max(0, min(100, total))  # Clamp to 0-100

        factors = {
            "sync_success_rate": sync_rate,
            "sync_points": sync_score,
            "avg_response_ms": avg_response,
            "response_points": response_score,
            "alarm_count": alarm_count,
            "alarm_points": alarm_score,
            "uptime_seconds": device.uptime,
            "uptime_points": uptime_score,
        }

        return total, factors

    async def check_device_health(self, device: Device) -> dict:
        """
        Check and update health for a single device.

        Returns:
            Dict with health check results
        """
        old_status = device.health_status
        old_score = device.health_score

        # Compute new score
        score, factors = await self.compute_health_score(device)
        status = get_status_from_score(score, device.is_online)

        # Update device
        device.health_score = score
        device.health_status = status
        device.last_health_check = datetime.utcnow()

        result = {
            "device_id": str(device.id),
            "serial_number": device.serial_number,
            "old_score": old_score,
            "new_score": score,
            "old_status": old_status,
            "new_status": status,
            "status_changed": old_status != status,
            "factors": factors,
        }

        return result

    async def check_all_devices(self) -> list:
        """Check health for all devices."""
        result = await self.db.execute(select(Device))
        devices = result.scalars().all()

        results = []
        for device in devices:
            try:
                check_result = await self.check_device_health(device)
                results.append(check_result)
            except Exception as e:
                logger.error(f"Error checking health for {device.serial_number}: {e}")
                results.append({
                    "device_id": str(device.id),
                    "serial_number": device.serial_number,
                    "error": str(e)
                })

        await self.db.commit()
        return results

    async def save_health_snapshot(self, device: Device, factors: dict):
        """Save hourly health snapshot."""
        snapshot = DeviceHealthHistory(
            device_id=device.id,
            timestamp=datetime.utcnow().replace(minute=0, second=0, microsecond=0),
            health_score=device.health_score,
            sync_success_rate=factors.get("sync_success_rate", 1.0),
            avg_response_ms=factors.get("avg_response_ms", 0),
            alarm_count=factors.get("alarm_count", 0),
            uptime_seconds=factors.get("uptime_seconds"),
        )
        self.db.add(snapshot)
