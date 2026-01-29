"""
Data purge background service.

Periodically deletes old audit logs and closed alarms based on
configured retention settings (auditing_purge_delay, alarm_purge_delay).
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.database import async_session_maker
from app.models import AuditLog, Alarm, Setting

logger = logging.getLogger(__name__)

_running = False
_task: Optional[asyncio.Task] = None

PURGE_INTERVAL = 86400  # 24 hours in seconds


async def purge_old_data():
    """Delete audit logs and closed alarms older than configured thresholds."""
    async with async_session_maker() as db:
        now = datetime.utcnow()

        # Get audit purge threshold
        result = await db.execute(
            select(Setting).where(Setting.key == "auditing_purge_delay")
        )
        setting = result.scalar_one_or_none()
        audit_days = int(setting.value) if setting and setting.value else 30

        # Get alarm purge threshold
        result = await db.execute(
            select(Setting).where(Setting.key == "alarm_purge_delay")
        )
        setting = result.scalar_one_or_none()
        alarm_days = int(setting.value) if setting and setting.value else 30

        # Purge old audit logs
        audit_threshold = now - timedelta(days=audit_days)
        audit_result = await db.execute(
            delete(AuditLog).where(AuditLog.created_at < audit_threshold)
        )
        audit_count = audit_result.rowcount

        # Purge old closed alarms (only closed ones)
        alarm_threshold = now - timedelta(days=alarm_days)
        alarm_result = await db.execute(
            delete(Alarm).where(
                Alarm.closing_date != None,
                Alarm.closing_date < alarm_threshold,
            )
        )
        alarm_count = alarm_result.rowcount

        await db.commit()

        if audit_count or alarm_count:
            logger.info(
                f"Purged {audit_count} audit logs (>{audit_days}d) "
                f"and {alarm_count} closed alarms (>{alarm_days}d)"
            )


async def purge_loop():
    """Background loop that periodically purges old data."""
    global _running
    logger.info("Data purge loop started")

    # Wait a bit on startup before first purge
    await asyncio.sleep(300)

    while _running:
        try:
            await purge_old_data()
        except Exception as e:
            logger.error(f"Error in data purge: {e}")

        await asyncio.sleep(PURGE_INTERVAL)


def start_purge_task():
    """Start the data purge background task."""
    global _running, _task
    if _running:
        return

    _running = True
    _task = asyncio.create_task(purge_loop())
    logger.info("Data purge task started")


def stop_purge_task():
    """Stop the data purge background task."""
    global _running, _task
    _running = False
    if _task:
        _task.cancel()
        _task = None
    logger.info("Data purge task stopped")
