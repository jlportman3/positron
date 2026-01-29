"""
Device offline detection background service.

Periodically checks all devices and marks them offline if they haven't
announced within the configured threshold (device_minutes_considered_active).
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import async_session_maker
from app.models import Device, Alarm, Setting

logger = logging.getLogger(__name__)

_running = False
_task: Optional[asyncio.Task] = None

CHECK_INTERVAL = 60  # seconds


async def check_offline_devices():
    """Check all devices and mark offline if last_seen exceeds threshold."""
    async with async_session_maker() as db:
        # Get thresholds from settings
        result = await db.execute(
            select(Setting).where(Setting.key == "device_minutes_considered_active")
        )
        setting = result.scalar_one_or_none()
        active_minutes = int(setting.value) if setting and setting.value else 5

        now = datetime.utcnow()
        threshold = now - timedelta(minutes=active_minutes)

        # Find online devices that haven't been seen recently
        result = await db.execute(
            select(Device).where(
                Device.is_online == True,
                Device.last_seen < threshold,
            )
        )
        stale_devices = result.scalars().all()

        for device in stale_devices:
            device.is_online = False
            logger.warning(
                f"Device {device.serial_number} ({device.name}) marked offline - "
                f"last seen {device.last_seen}, threshold {active_minutes} minutes"
            )

            # Create alarm for device going offline
            alarm = Alarm(
                device_id=device.id,
                gam_id=f"OFFLINE_{device.serial_number}",
                cond_type="DeviceOffline",
                severity="CR",
                serv_aff="SA",
                details=f"Device has not announced in {active_minutes} minutes",
                is_manual=False,
                occurred_at=now,
            )

            # Check if there's already an open offline alarm
            existing = await db.execute(
                select(Alarm).where(
                    Alarm.device_id == device.id,
                    Alarm.gam_id == f"OFFLINE_{device.serial_number}",
                    Alarm.closing_date == None,
                )
            )
            if not existing.scalar_one_or_none():
                db.add(alarm)

        if stale_devices:
            await db.commit()
            logger.info(f"Marked {len(stale_devices)} device(s) offline")


async def offline_detection_loop():
    """Background loop that checks for offline devices."""
    global _running
    logger.info("Offline detection loop started")

    while _running:
        try:
            await check_offline_devices()
        except Exception as e:
            logger.error(f"Error in offline detection: {e}")

        await asyncio.sleep(CHECK_INTERVAL)


def start_offline_detection():
    """Start the offline detection background task."""
    global _running, _task
    if _running:
        return

    _running = True
    _task = asyncio.create_task(offline_detection_loop())
    logger.info("Offline detection task started")


def stop_offline_detection():
    """Stop the offline detection background task."""
    global _running, _task
    _running = False
    if _task:
        _task.cancel()
        _task = None
    logger.info("Offline detection task stopped")
