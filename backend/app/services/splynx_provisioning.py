"""
Splynx provisioning service.

Handles:
- Background task to retry Splynx lookups for new endpoints
- Auto-provisioning subscribers when matches are found
- Creating customer notes and QC tickets in Splynx
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import async_session_maker
from app.models import Endpoint, Subscriber, Setting, SplynxLookupTask
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


async def create_lookup_task_for_endpoint(db: AsyncSession, endpoint: Endpoint) -> SplynxLookupTask:
    """Create a new lookup task for an endpoint."""
    task = SplynxLookupTask(
        endpoint_id=endpoint.id,
        mac_address=endpoint.mac_address,
        status="pending",
        attempts=0,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    logger.info(f"Created lookup task for endpoint {endpoint.mac_address}")
    return task


async def process_pending_tasks():
    """Process all pending Splynx lookup tasks."""
    async with async_session_maker() as db:
        # Get settings
        auto_provision = await get_setting(db, "splynx_auto_provision", "false") == "true"
        retry_hours = int(await get_setting(db, "splynx_retry_duration_hours", "24"))

        # Create Splynx client
        client = await create_splynx_client(db)
        if not client:
            logger.debug("Splynx not configured, skipping lookup tasks")
            return

        try:
            # Get pending tasks
            cutoff_time = datetime.utcnow() - timedelta(hours=retry_hours)
            result = await db.execute(
                select(SplynxLookupTask).where(
                    and_(
                        SplynxLookupTask.status == "pending",
                        SplynxLookupTask.created_at > cutoff_time,
                    )
                )
            )
            tasks = result.scalars().all()

            if not tasks:
                return

            logger.info(f"Processing {len(tasks)} pending Splynx lookup tasks")

            for task in tasks:
                await process_single_task(db, client, task, auto_provision)

            await db.commit()

        except Exception as e:
            logger.error(f"Error processing lookup tasks: {e}")
            await db.rollback()
        finally:
            await client.close()

        # Expire old tasks
        await expire_old_tasks(db, retry_hours)


async def process_single_task(
    db: AsyncSession,
    client: SplynxClient,
    task: SplynxLookupTask,
    auto_provision: bool,
):
    """Process a single lookup task."""
    task.attempts += 1
    task.last_attempt_at = datetime.utcnow()

    try:
        # Search for MAC address in Splynx inventory
        inventory = await client.search_inventory_by_mac(task.mac_address)

        if inventory:
            # Found! Get customer details
            customer_id = inventory.get("customer_id")
            if customer_id:
                customer = await client.get_customer(customer_id)
                services = await client.get_customer_services(customer_id)

                # Update task with found data
                task.status = "found"
                task.found_customer_id = customer_id
                task.found_customer_name = customer.get("name") if customer else None
                task.found_inventory_id = inventory.get("id")

                if services and len(services) > 0:
                    task.found_service_id = services[0].get("id")
                    task.found_tariff_name = services[0].get("tariff_name")

                task.completed_at = datetime.utcnow()

                logger.info(
                    f"Found Splynx match for {task.mac_address}: "
                    f"customer={task.found_customer_name} (ID={customer_id})"
                )

                if auto_provision:
                    await auto_provision_subscriber(db, client, task)
            else:
                logger.debug(f"Inventory found but no customer_id for {task.mac_address}")
        else:
            logger.debug(f"No Splynx match for {task.mac_address} (attempt {task.attempts})")

    except Exception as e:
        task.error_message = str(e)
        logger.error(f"Error looking up {task.mac_address}: {e}")


async def auto_provision_subscriber(
    db: AsyncSession,
    client: SplynxClient,
    task: SplynxLookupTask,
):
    """Auto-provision a subscriber from Splynx data."""
    try:
        # Get endpoint
        result = await db.execute(
            select(Endpoint).where(Endpoint.id == task.endpoint_id)
        )
        endpoint = result.scalar_one_or_none()
        if not endpoint:
            logger.error(f"Endpoint {task.endpoint_id} not found for provisioning")
            return

        # Get provisioning settings
        default_bw_profile = await get_setting(db, "splynx_default_bandwidth_profile", "Unthrottled")
        default_vlan = await get_setting(db, "splynx_default_vlan", "100")

        # Format subscriber name as "CUSTOMER_ID CUSTOMER_NAME"
        subscriber_name = f"{task.found_customer_id} {task.found_customer_name or 'Unknown'}"

        # Check if subscriber already exists for this endpoint
        result = await db.execute(
            select(Subscriber).where(
                and_(
                    Subscriber.device_id == endpoint.device_id,
                    Subscriber.endpoint_mac_address == task.mac_address,
                )
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            logger.info(f"Subscriber already exists for {task.mac_address}, skipping creation")
            task.status = "provisioned"
            return

        # Create subscriber record
        subscriber = Subscriber(
            device_id=endpoint.device_id,
            name=subscriber_name,
            endpoint_json_id=endpoint.conf_endpoint_id,
            endpoint_name=endpoint.conf_endpoint_name,
            endpoint_mac_address=task.mac_address,
            bw_profile_name=default_bw_profile,
            port1_vlan_id=default_vlan,
            vlan_is_tagged=False,
            trunk_mode=True,
            splynx_customer_id=task.found_customer_id,
            splynx_service_id=task.found_service_id,
        )
        db.add(subscriber)

        logger.info(f"Created subscriber {subscriber_name} for endpoint {task.mac_address}")

        # TODO: Push subscriber to device via JSON-RPC
        # This requires the device sync service to push changes

        # Write customer note to Splynx
        if task.found_customer_id:
            await write_provisioning_note(client, task, endpoint)

        # Create QC ticket in Splynx
        await create_qc_ticket(db, client, task)

        task.status = "provisioned"

    except Exception as e:
        logger.error(f"Error auto-provisioning for {task.mac_address}: {e}")
        task.error_message = f"Auto-provision failed: {str(e)}"


async def write_provisioning_note(
    client: SplynxClient,
    task: SplynxLookupTask,
    endpoint: Endpoint,
):
    """Write a provisioning note to the Splynx customer record."""
    note = f"""=== GAM Provisioning ===
Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
Provisioned By: Auto-provision

CPE MAC: {task.mac_address}
CPE Model: {endpoint.model_string or endpoint.model_type or 'Unknown'}

Service Configuration:
- Bandwidth Profile: {task.found_tariff_name or 'Default'}

Status: Active
"""
    try:
        await client.add_customer_note(task.found_customer_id, note)
        logger.info(f"Added provisioning note to customer {task.found_customer_id}")
    except Exception as e:
        logger.error(f"Failed to add customer note: {e}")


async def create_qc_ticket(
    db: AsyncSession,
    client: SplynxClient,
    task: SplynxLookupTask,
):
    """Create a QC ticket in Splynx."""
    assignee_id = await get_setting(db, "splynx_qc_ticket_assignee_id")

    subject = f"Install QC: {task.found_customer_name}"
    body = f"""New GAM provisioning completed - please perform QC visit.

Customer: {task.found_customer_name}
Customer ID: {task.found_customer_id}
CPE MAC: {task.mac_address}

=== QC Checklist ===
[ ] Signal quality verified (PHY rate acceptable)
[ ] Speed test performed and meets plan requirements
[ ] WiFi router configured and tested
[ ] Customer shown how to reboot equipment if needed
[ ] Customer contact information confirmed
[ ] Service address verified correct
[ ] Equipment location documented
[ ] Customer satisfaction confirmed

Provisioned: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""

    ticket_data = {
        "subject": subject,
        "message": body,
        "customer_id": task.found_customer_id,
        "priority": "normal",
    }

    if assignee_id:
        ticket_data["assigned_to"] = int(assignee_id)

    try:
        await client.create_ticket(ticket_data)
        logger.info(f"Created QC ticket for customer {task.found_customer_id}")
    except Exception as e:
        logger.error(f"Failed to create QC ticket: {e}")


async def expire_old_tasks(db: AsyncSession, retry_hours: int):
    """Mark old pending tasks as expired."""
    cutoff_time = datetime.utcnow() - timedelta(hours=retry_hours)
    result = await db.execute(
        select(SplynxLookupTask).where(
            and_(
                SplynxLookupTask.status == "pending",
                SplynxLookupTask.created_at <= cutoff_time,
            )
        )
    )
    expired_tasks = result.scalars().all()

    for task in expired_tasks:
        task.status = "expired"
        task.completed_at = datetime.utcnow()
        logger.info(f"Expired lookup task for {task.mac_address} after {retry_hours} hours")

    if expired_tasks:
        await db.commit()


async def background_lookup_loop():
    """Background task that runs every minute to process pending lookups."""
    global _running
    logger.info("Starting Splynx lookup background task")

    while _running:
        try:
            await process_pending_tasks()
        except Exception as e:
            logger.error(f"Error in Splynx lookup loop: {e}")

        # Wait 1 minute before next check
        await asyncio.sleep(60)

    logger.info("Splynx lookup background task stopped")


def start_background_task():
    """Start the background lookup task."""
    global _running, _task
    if _running:
        return

    _running = True
    _task = asyncio.create_task(background_lookup_loop())
    logger.info("Splynx background task started")


def stop_background_task():
    """Stop the background lookup task."""
    global _running, _task
    _running = False
    if _task:
        _task.cancel()
        _task = None
    logger.info("Splynx background task stopped")
