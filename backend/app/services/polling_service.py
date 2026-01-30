"""
Device polling background service.

Periodically syncs all online devices using the polling intervals
configured in settings (polling_endpoints_interval, polling_subscribers_interval, etc.).
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.models import Device, Setting
from app.rpc.client import create_client_for_device
from app.services.device_sync import DeviceSyncService

logger = logging.getLogger(__name__)

_running = False
_task: Optional[asyncio.Task] = None

# How often the loop checks for devices that need polling (seconds)
LOOP_INTERVAL = 30


async def _get_interval_minutes(db: AsyncSession, key: str, default: int) -> int:
    """Get a polling interval setting in minutes."""
    result = await db.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    try:
        return int(setting.value) if setting and setting.value else default
    except (ValueError, TypeError):
        return default


async def poll_device(device: Device, db: AsyncSession) -> None:
    """Run a full sync on a single device."""
    try:
        sync_service = DeviceSyncService(db)
        await sync_service.sync_device(device)
        logger.debug(f"Polled {device.name} ({device.serial_number}) successfully")
    except Exception as e:
        logger.warning(f"Poll failed for {device.name} ({device.serial_number}): {e}")


async def polling_loop():
    """Background loop that polls devices based on configured intervals."""
    global _running
    logger.info("Device polling loop started")

    while _running:
        try:
            async with async_session_maker() as db:
                # Read the endpoint polling interval (controls full sync frequency)
                interval = await _get_interval_minutes(db, "polling_endpoints_interval", 5)
                threshold = datetime.utcnow() - timedelta(minutes=interval)

                # Find online devices that haven't been synced within the interval
                result = await db.execute(
                    select(Device).where(
                        Device.is_online == True,
                        (Device.last_endpoint_brief_pulled == None) |
                        (Device.last_endpoint_brief_pulled < threshold),
                    )
                )
                devices = result.scalars().all()

                if devices:
                    logger.info(
                        f"Polling {len(devices)} device(s) "
                        f"(interval={interval}min)"
                    )
                    for device in devices:
                        if not _running:
                            break
                        await poll_device(device, db)

        except Exception as e:
            logger.error(f"Error in polling loop: {e}")

        await asyncio.sleep(LOOP_INTERVAL)

    logger.info("Device polling loop stopped")


def start_polling():
    """Start the device polling background task."""
    global _running, _task
    if _running:
        return
    _running = True
    _task = asyncio.create_task(polling_loop())
    logger.info("Device polling task started")


def stop_polling():
    """Stop the device polling background task."""
    global _running, _task
    _running = False
    if _task:
        _task.cancel()
        _task = None
    logger.info("Device polling task stopped")
