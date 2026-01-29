"""
Splynx reconciliation service.

Runs daily to compare GAM subscribers with Splynx inventory and
creates tickets for any mismatches.
"""
import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import async_session_maker
from app.models import Subscriber, Setting
from app.integrations.splynx_client import SplynxClient

logger = logging.getLogger(__name__)

# Global flag to control background task
_running = False
_task: Optional[asyncio.Task] = None


async def get_setting(db: AsyncSession, key: str, default: str = "") -> str:
    """Get a setting value from the database."""
    result = await db.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    return setting.value if setting and setting.value else default


async def create_splynx_client(db: AsyncSession) -> Optional[SplynxClient]:
    """Create a SplynxClient from database settings."""
    api_url = await get_setting(db, "splynx_api_url")
    api_key = await get_setting(db, "splynx_api_key")
    api_secret = await get_setting(db, "splynx_api_secret")

    if not all([api_url, api_key, api_secret]):
        return None

    return SplynxClient(
        base_url=api_url,
        api_key=api_key,
        api_secret=api_secret,
    )


async def run_reconciliation():
    """Run the daily reconciliation between GAM and Splynx."""
    logger.info("Starting daily Splynx reconciliation")

    async with async_session_maker() as db:
        client = await create_splynx_client(db)
        if not client:
            logger.info("Splynx not configured, skipping reconciliation")
            return

        try:
            mismatches = await find_mismatches(db, client)

            if mismatches:
                await create_mismatch_ticket(client, mismatches)
                logger.info(f"Reconciliation complete: {len(mismatches)} mismatches found")
            else:
                logger.info("Reconciliation complete: no mismatches found")

        except Exception as e:
            logger.error(f"Error during reconciliation: {e}")
        finally:
            await client.close()


async def find_mismatches(
    db: AsyncSession,
    client: SplynxClient,
) -> List[Dict[str, Any]]:
    """Find mismatches between GAM subscribers and Splynx inventory."""
    mismatches = []

    # Get all subscribers with Splynx customer IDs
    result = await db.execute(
        select(Subscriber).where(Subscriber.splynx_customer_id.isnot(None))
    )
    subscribers = result.scalars().all()

    if not subscribers:
        logger.debug("No subscribers with Splynx IDs to reconcile")
        return mismatches

    # Get all inventory items from Splynx
    try:
        splynx_inventory = await client.get_all_inventory_with_customers()
    except Exception as e:
        logger.error(f"Failed to fetch Splynx inventory: {e}")
        return mismatches

    # Build lookup maps
    # MAC address -> inventory item
    inventory_by_mac = {}
    for item in splynx_inventory:
        mac = item.get("mac", "").lower().replace(":", "").replace("-", "")
        if mac:
            inventory_by_mac[mac] = item

    # Check each GAM subscriber
    for subscriber in subscribers:
        if not subscriber.endpoint_mac_address:
            continue

        # Normalize MAC address
        sub_mac = subscriber.endpoint_mac_address.lower().replace(":", "").replace("-", "")

        # Check if exists in Splynx
        splynx_item = inventory_by_mac.get(sub_mac)

        if not splynx_item:
            # Orphan in GAM - has splynx_customer_id but not in Splynx inventory
            mismatches.append({
                "type": "orphan_gam",
                "description": "GAM subscriber has Splynx ID but MAC not in Splynx inventory",
                "gam_subscriber": subscriber.name,
                "mac_address": subscriber.endpoint_mac_address,
                "gam_splynx_id": subscriber.splynx_customer_id,
            })
            continue

        # Get customer details
        splynx_customer_id = splynx_item.get("customer_id")
        if splynx_customer_id and splynx_customer_id != subscriber.splynx_customer_id:
            # Customer ID mismatch
            mismatches.append({
                "type": "customer_mismatch",
                "description": "Customer ID differs between GAM and Splynx",
                "gam_subscriber": subscriber.name,
                "mac_address": subscriber.endpoint_mac_address,
                "gam_customer_id": subscriber.splynx_customer_id,
                "splynx_customer_id": splynx_customer_id,
            })

    # Check for orphans in Splynx (has customer assignment but no GAM subscriber)
    gam_macs = {
        s.endpoint_mac_address.lower().replace(":", "").replace("-", "")
        for s in subscribers
        if s.endpoint_mac_address
    }

    for item in splynx_inventory:
        mac = item.get("mac", "").lower().replace(":", "").replace("-", "")
        customer_id = item.get("customer_id")

        if mac and customer_id and mac not in gam_macs:
            # This inventory item is assigned to a customer but has no GAM subscriber
            # This could be normal (CPE not yet installed) so we log but don't create ticket
            logger.debug(
                f"Splynx inventory {item.get('id')} (MAC {mac}) assigned to customer "
                f"{customer_id} but no GAM subscriber exists"
            )

    return mismatches


async def create_mismatch_ticket(
    client: SplynxClient,
    mismatches: List[Dict[str, Any]],
):
    """Create a reconciliation ticket in Splynx for all mismatches."""
    subject = f"GAM/Splynx Reconciliation Alert - {len(mismatches)} issues found"

    body_lines = [
        "Daily reconciliation found the following mismatches:\n",
    ]

    for m in mismatches:
        body_lines.append(f"- {m['type']}: {m['gam_subscriber']} ({m['mac_address']})")
        body_lines.append(f"  {m['description']}")
        if m['type'] == 'customer_mismatch':
            body_lines.append(f"  GAM: Customer ID {m['gam_customer_id']}")
            body_lines.append(f"  Splynx: Customer ID {m['splynx_customer_id']}")
        elif m['type'] == 'orphan_gam':
            body_lines.append(f"  GAM: Customer ID {m['gam_splynx_id']}")
        body_lines.append("")

    body_lines.append("\nPlease review and correct as needed.")

    ticket_data = {
        "subject": subject,
        "message": "\n".join(body_lines),
        "priority": "normal",
    }

    try:
        await client.create_ticket(ticket_data)
        logger.info(f"Created reconciliation ticket with {len(mismatches)} issues")
    except Exception as e:
        logger.error(f"Failed to create reconciliation ticket: {e}")


def parse_time_setting(time_str: str) -> time:
    """Parse a time setting like '02:00' into a time object."""
    try:
        parts = time_str.split(":")
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        return time(hour=hour, minute=minute)
    except (ValueError, IndexError):
        return time(hour=2, minute=0)  # Default to 2:00 AM


def seconds_until_time(target_time: time) -> float:
    """Calculate seconds until the next occurrence of target_time."""
    now = datetime.now()
    target = datetime.combine(now.date(), target_time)

    # If target time has passed today, schedule for tomorrow
    if now >= target:
        target = target + timedelta(days=1)

    return (target - now).total_seconds()


async def background_reconciliation_loop():
    """Background task that runs reconciliation daily at configured time."""
    global _running
    logger.info("Starting Splynx reconciliation background task")

    while _running:
        try:
            # Get reconciliation time from settings
            async with async_session_maker() as db:
                time_str = await get_setting(db, "splynx_reconciliation_time", "02:00")

            target_time = parse_time_setting(time_str)
            wait_seconds = seconds_until_time(target_time)

            logger.info(
                f"Reconciliation scheduled for {target_time.strftime('%H:%M')}, "
                f"waiting {wait_seconds / 3600:.1f} hours"
            )

            # Wait until target time (checking every hour in case settings change)
            while wait_seconds > 0 and _running:
                sleep_time = min(wait_seconds, 3600)  # Check hourly
                await asyncio.sleep(sleep_time)
                wait_seconds -= sleep_time

                # Re-check settings in case time was changed
                if wait_seconds > 0:
                    async with async_session_maker() as db:
                        new_time_str = await get_setting(db, "splynx_reconciliation_time", "02:00")
                    if new_time_str != time_str:
                        time_str = new_time_str
                        target_time = parse_time_setting(time_str)
                        wait_seconds = seconds_until_time(target_time)

            if _running:
                await run_reconciliation()

        except Exception as e:
            logger.error(f"Error in reconciliation loop: {e}")
            # Wait an hour before retrying on error
            await asyncio.sleep(3600)

    logger.info("Splynx reconciliation background task stopped")


def start_reconciliation_task():
    """Start the background reconciliation task."""
    global _running, _task
    if _running:
        return

    _running = True
    _task = asyncio.create_task(background_reconciliation_loop())
    logger.info("Splynx reconciliation task started")


def stop_reconciliation_task():
    """Stop the background reconciliation task."""
    global _running, _task
    _running = False
    if _task:
        _task.cancel()
        _task = None
    logger.info("Splynx reconciliation task stopped")
