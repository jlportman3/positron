"""Background task for periodic health checks."""
import asyncio
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.services.health_monitor import HealthMonitorService
from app.models import Setting, Device

logger = logging.getLogger(__name__)

# Default interval in minutes
DEFAULT_INTERVAL = 5


async def get_health_check_interval(db: AsyncSession) -> int:
    """Get health check interval from settings."""
    from sqlalchemy import select
    result = await db.execute(
        select(Setting).where(Setting.key == "health_check_interval_minutes")
    )
    setting = result.scalar_one_or_none()
    if setting and setting.value:
        try:
            return int(setting.value)
        except ValueError:
            pass
    return DEFAULT_INTERVAL


async def run_health_check():
    """Run a single health check cycle."""
    async with async_session_maker() as db:
        service = HealthMonitorService(db)
        results = await service.check_all_devices()

        # Log summary
        status_changed = [r for r in results if r.get("status_changed")]
        if status_changed:
            for r in status_changed:
                logger.info(
                    f"Health status changed: {r['serial_number']} "
                    f"{r['old_status']} -> {r['new_status']} (score: {r['new_score']})"
                )

        # Save hourly snapshots if on the hour
        now = datetime.utcnow()
        if now.minute < DEFAULT_INTERVAL:
            from sqlalchemy import select

            result = await db.execute(select(Device))
            devices = result.scalars().all()

            for device in devices:
                # Find the factors from results
                device_result = next(
                    (r for r in results if r.get("device_id") == str(device.id)),
                    None
                )
                if device_result and "factors" in device_result:
                    await service.save_health_snapshot(device, device_result["factors"])

            await db.commit()
            logger.info(f"Saved health snapshots for {len(devices)} devices")

        return results


async def health_check_loop():
    """Main loop for health checks."""
    logger.info("Health check background task started")

    while True:
        try:
            # Get interval from settings
            async with async_session_maker() as db:
                interval = await get_health_check_interval(db)

            # Run health check
            await run_health_check()

            # Sleep until next check
            await asyncio.sleep(interval * 60)

        except asyncio.CancelledError:
            logger.info("Health check task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in health check loop: {e}")
            await asyncio.sleep(60)  # Wait 1 minute on error


# Task handle for cancellation
_health_check_task = None


def start_health_check_task():
    """Start the health check background task."""
    global _health_check_task
    _health_check_task = asyncio.create_task(health_check_loop())
    return _health_check_task


def stop_health_check_task():
    """Stop the health check background task."""
    global _health_check_task
    if _health_check_task:
        _health_check_task.cancel()
        _health_check_task = None
