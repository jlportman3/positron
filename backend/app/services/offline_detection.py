"""
Device offline detection background service.

Periodically checks all devices and marks them offline if they haven't
announced within the configured threshold (device_minutes_considered_active).

Also performs ICMP ping checks as a secondary liveness probe — if a device
responds to ping, it is kept online even if the announcement is late.
"""
import asyncio
import logging
import subprocess
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


async def ping_host(ip: str, timeout: int = 2) -> bool:
    """ICMP ping a host. Returns True if reachable."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "ping", "-c", "1", "-W", str(timeout), ip,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()
        return proc.returncode == 0
    except Exception:
        return False


async def ping_devices(devices: list[Device]) -> dict:
    """Ping multiple devices concurrently. Returns {device_id: reachable}."""
    tasks = {}
    for device in devices:
        if device.ip_address:
            tasks[device.id] = asyncio.create_task(ping_host(device.ip_address))

    results = {}
    for device_id, task in tasks.items():
        results[device_id] = await task
    return results


async def check_offline_devices():
    """Check all devices and mark offline if last_seen exceeds threshold.

    Uses both announcement staleness and ICMP ping as liveness checks.
    A device stays online if either check passes.
    """
    async with async_session_maker() as db:
        # Get thresholds from settings
        result = await db.execute(
            select(Setting).where(Setting.key == "device_minutes_considered_active")
        )
        setting = result.scalar_one_or_none()
        active_minutes = int(setting.value) if setting and setting.value else 5

        now = datetime.utcnow()
        threshold = now - timedelta(minutes=active_minutes)

        # Find online devices that haven't announced recently
        result = await db.execute(
            select(Device).where(
                Device.is_online == True,
                Device.last_seen < threshold,
            )
        )
        stale_devices = result.scalars().all()

        if not stale_devices:
            return

        # Ping stale devices before marking offline
        ping_results = await ping_devices(stale_devices)

        for device in stale_devices:
            if ping_results.get(device.id, False):
                # Device responds to ping — keep online, update last_seen
                device.last_seen = now
                logger.info(
                    f"Device {device.serial_number} ({device.name}) stale announcement "
                    f"but responds to ping — keeping online"
                )
                continue

            device.is_online = False
            logger.warning(
                f"Device {device.serial_number} ({device.name}) marked offline - "
                f"last seen {device.last_seen}, no ping response, threshold {active_minutes} minutes"
            )

            # Create alarm for device going offline
            alarm = Alarm(
                device_id=device.id,
                gam_id=f"OFFLINE_{device.serial_number}",
                cond_type="DeviceOffline",
                severity="CR",
                serv_aff="SA",
                details=f"Device has not announced in {active_minutes} minutes and does not respond to ping",
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

        await db.commit()

        marked_offline = [d for d in stale_devices if not ping_results.get(d.id, False)]
        kept_online = [d for d in stale_devices if ping_results.get(d.id, False)]
        if marked_offline:
            logger.info(f"Marked {len(marked_offline)} device(s) offline")
        if kept_online:
            logger.info(f"Kept {len(kept_online)} device(s) online via ping")


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
