"""
Splynx integration API endpoints.

- Accepts webhooks from Splynx for customer, service, and inventory provisioning.
- Provides outbound API calls to Splynx for lookups and provisioning.
"""
import logging
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.core.config import settings
from app.models import Setting, Endpoint, Subscriber, Device
from app.integrations.splynx_client import (
    SplynxClient,
    SplynxApiError,
    create_splynx_client_from_settings,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/splynx", tags=["Splynx Integration"])


# ============================================================================
# Pydantic Models for Webhook Data
# ============================================================================

class SplynxWebhookPayload(BaseModel):
    """Base Splynx webhook payload."""
    event: str
    timestamp: Optional[str] = None
    data: dict


class CustomerData(BaseModel):
    """Splynx customer data."""
    id: int
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    address: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[str] = None
    location_id: Optional[int] = None
    partner_id: Optional[int] = None
    billing_type: Optional[str] = None


class ServiceData(BaseModel):
    """Splynx service data."""
    id: int
    customer_id: int
    service_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    tariff_id: Optional[int] = None
    tariff_name: Optional[str] = None
    mac_address: Optional[str] = None
    login: Optional[str] = None
    password: Optional[str] = None
    ip_address: Optional[str] = None
    ipv6_address: Optional[str] = None
    download_speed: Optional[int] = None
    upload_speed: Optional[int] = None


class InventoryData(BaseModel):
    """Splynx inventory item data."""
    id: int
    item_type: Optional[str] = None
    item_name: Optional[str] = None
    serial_number: Optional[str] = None
    mac_address: Optional[str] = None
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    status: Optional[str] = None  # in_stock, assigned, sold, rma, etc.
    location_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    vendor: Optional[str] = None
    model: Optional[str] = None
    notes: Optional[str] = None


# ============================================================================
# Webhook Secret Verification
# ============================================================================

async def verify_splynx_secret(
    x_splynx_secret: Optional[str] = Header(None, alias="X-Splynx-Secret"),
    db: AsyncSession = Depends(get_db),
) -> bool:
    """Verify the Splynx webhook secret."""
    result = await db.execute(
        select(Setting).where(Setting.key == "splynx_webhook_secret")
    )
    setting = result.scalar_one_or_none()

    if not setting or not setting.value:
        logger.warning("Splynx webhook received but no secret configured - allowing")
        return True

    if x_splynx_secret != setting.value:
        logger.warning("Invalid Splynx webhook secret received")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook secret"
        )

    return True


# ============================================================================
# Main Webhook Endpoint
# ============================================================================

@router.post("/webhook")
async def splynx_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _verified: bool = Depends(verify_splynx_secret),
):
    """
    Receive webhooks from Splynx.

    Supported events:

    Customer Events:
    - customer.created
    - customer.updated
    - customer.deleted
    - customer.blocked
    - customer.activated

    Service Events:
    - service.created
    - service.updated
    - service.deleted
    - service.activated
    - service.suspended
    - service.stopped

    Inventory Events:
    - inventory.created
    - inventory.updated
    - inventory.deleted
    - inventory.assigned (to customer)
    - inventory.unassigned (from customer)
    - inventory.status_changed
    """
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse Splynx webhook payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )

    event = payload.get("event", "unknown")
    data = payload.get("data", {})

    logger.info(f"Received Splynx webhook: {event}")
    logger.debug(f"Webhook payload: {payload}")

    # Route to appropriate handler
    if event.startswith("customer."):
        return await handle_customer_event(event, data, db)
    elif event.startswith("service."):
        return await handle_service_event(event, data, db)
    elif event.startswith("inventory."):
        return await handle_inventory_event(event, data, db)
    else:
        logger.warning(f"Unknown Splynx webhook event: {event}")
        return {
            "status": "ignored",
            "message": f"Unknown event type: {event}"
        }


# ============================================================================
# Customer Event Handlers
# ============================================================================

async def handle_customer_event(event: str, data: dict, db: AsyncSession):
    """Handle customer-related webhooks."""
    customer_id = data.get("id")
    customer_name = data.get("name", "Unknown")

    if event == "customer.created":
        logger.info(f"Splynx customer created: {customer_id} - {customer_name}")
        return {
            "status": "received",
            "event": event,
            "customer_id": customer_id,
            "customer_name": customer_name,
            "action": "logged"
        }

    elif event == "customer.updated":
        logger.info(f"Splynx customer updated: {customer_id} - {customer_name}")
        # Update any subscribers linked to this customer
        updated = await update_subscribers_for_customer(customer_id, data, db)
        return {
            "status": "received",
            "event": event,
            "customer_id": customer_id,
            "subscribers_updated": updated,
            "action": "processed"
        }

    elif event == "customer.deleted":
        logger.info(f"Splynx customer deleted: {customer_id}")
        return {
            "status": "received",
            "event": event,
            "customer_id": customer_id,
            "action": "logged"
        }

    elif event == "customer.blocked":
        logger.info(f"Splynx customer blocked: {customer_id}")
        # Could disable all subscribers for this customer
        return {
            "status": "received",
            "event": event,
            "customer_id": customer_id,
            "action": "logged"
        }

    elif event == "customer.activated":
        logger.info(f"Splynx customer activated: {customer_id}")
        return {
            "status": "received",
            "event": event,
            "customer_id": customer_id,
            "action": "logged"
        }

    return {"status": "ignored", "event": event}


async def update_subscribers_for_customer(customer_id: int, data: dict, db: AsyncSession) -> int:
    """Update subscriber records when customer info changes."""
    # Find subscribers linked to this Splynx customer
    result = await db.execute(
        select(Subscriber).where(Subscriber.splynx_customer_id == customer_id)
    )
    subscribers = result.scalars().all()

    updated_count = 0
    customer_name = data.get("name")

    for subscriber in subscribers:
        if customer_name and subscriber.name != customer_name:
            subscriber.name = customer_name
            subscriber.updated_at = datetime.utcnow()
            updated_count += 1

    if updated_count > 0:
        await db.commit()

    return updated_count


# ============================================================================
# Service Event Handlers
# ============================================================================

async def handle_service_event(event: str, data: dict, db: AsyncSession):
    """Handle service-related webhooks."""
    service_id = data.get("id")
    customer_id = data.get("customer_id")
    mac_address = data.get("mac_address")
    tariff_name = data.get("tariff_name")

    if event == "service.created":
        logger.info(f"Splynx service created: {service_id} for customer {customer_id}")
        # Try to auto-provision if MAC matches an endpoint
        result = await auto_provision_subscriber(data, db)
        return {
            "status": "received",
            "event": event,
            "service_id": service_id,
            "customer_id": customer_id,
            "mac_address": mac_address,
            "auto_provisioned": result.get("provisioned", False),
            "action": "processed"
        }

    elif event == "service.updated":
        logger.info(f"Splynx service updated: {service_id}")
        # Update subscriber bandwidth if tariff changed
        updated = await update_subscriber_from_service(service_id, data, db)
        return {
            "status": "received",
            "event": event,
            "service_id": service_id,
            "subscriber_updated": updated,
            "action": "processed"
        }

    elif event == "service.activated":
        logger.info(f"Splynx service activated: {service_id}")
        # Enable subscriber on device
        return {
            "status": "received",
            "event": event,
            "service_id": service_id,
            "action": "logged"
        }

    elif event == "service.suspended":
        logger.info(f"Splynx service suspended: {service_id}")
        # Could disable subscriber on device
        return {
            "status": "received",
            "event": event,
            "service_id": service_id,
            "action": "logged"
        }

    elif event == "service.stopped":
        logger.info(f"Splynx service stopped: {service_id}")
        return {
            "status": "received",
            "event": event,
            "service_id": service_id,
            "action": "logged"
        }

    elif event == "service.deleted":
        logger.info(f"Splynx service deleted: {service_id}")
        return {
            "status": "received",
            "event": event,
            "service_id": service_id,
            "action": "logged"
        }

    return {"status": "ignored", "event": event}


async def auto_provision_subscriber(data: dict, db: AsyncSession) -> dict:
    """Attempt to auto-provision a subscriber based on MAC address."""
    mac_address = data.get("mac_address")
    if not mac_address:
        return {"provisioned": False, "reason": "no_mac"}

    # Normalize MAC address
    mac_normalized = mac_address.upper().replace(":", "").replace("-", "")

    # Look for endpoint with matching MAC
    result = await db.execute(
        select(Endpoint).where(
            or_(
                Endpoint.mac_address == mac_address,
                Endpoint.mac_address == mac_normalized,
                Endpoint.mac_address == mac_address.upper(),
            )
        )
    )
    endpoint = result.scalar_one_or_none()

    if not endpoint:
        logger.info(f"No endpoint found for MAC {mac_address}")
        return {"provisioned": False, "reason": "endpoint_not_found"}

    # Check if subscriber already exists for this endpoint
    existing = await db.execute(
        select(Subscriber).where(Subscriber.endpoint_id == endpoint.id)
    )
    if existing.scalar_one_or_none():
        logger.info(f"Subscriber already exists for endpoint {endpoint.id}")
        return {"provisioned": False, "reason": "subscriber_exists"}

    logger.info(f"Auto-provisioning subscriber for endpoint {endpoint.id}")
    # Would create subscriber here - for now just log
    return {
        "provisioned": False,
        "reason": "auto_provision_disabled",
        "endpoint_id": str(endpoint.id),
        "endpoint_mac": endpoint.mac_address
    }


async def update_subscriber_from_service(service_id: int, data: dict, db: AsyncSession) -> bool:
    """Update subscriber when service changes in Splynx."""
    result = await db.execute(
        select(Subscriber).where(Subscriber.splynx_service_id == service_id)
    )
    subscriber = result.scalar_one_or_none()

    if not subscriber:
        return False

    # Update subscriber from service data
    updated = False
    if data.get("tariff_name") and subscriber.bw_profile_name != data.get("tariff_name"):
        # Would update bandwidth profile here
        updated = True

    return updated


# ============================================================================
# Inventory Event Handlers
# ============================================================================

async def handle_inventory_event(event: str, data: dict, db: AsyncSession):
    """Handle inventory-related webhooks."""
    inventory_id = data.get("id")
    item_name = data.get("item_name", data.get("name", "Unknown"))
    serial_number = data.get("serial_number")
    mac_address = data.get("mac_address")
    customer_id = data.get("customer_id")
    customer_name = data.get("customer_name")
    item_status = data.get("status")

    if event == "inventory.created":
        logger.info(f"Splynx inventory created: {inventory_id} - {item_name} (SN: {serial_number})")
        return {
            "status": "received",
            "event": event,
            "inventory_id": inventory_id,
            "item_name": item_name,
            "serial_number": serial_number,
            "mac_address": mac_address,
            "action": "logged"
        }

    elif event == "inventory.updated":
        logger.info(f"Splynx inventory updated: {inventory_id} - {item_name}")
        # Check if MAC changed or customer assignment changed
        result = await process_inventory_update(data, db)
        return {
            "status": "received",
            "event": event,
            "inventory_id": inventory_id,
            "item_name": item_name,
            "customer_id": customer_id,
            "endpoint_found": result.get("endpoint_found", False),
            "action": "processed"
        }

    elif event == "inventory.assigned":
        logger.info(f"Splynx inventory assigned: {inventory_id} to customer {customer_id} ({customer_name})")
        # This is the key event - CPE assigned to customer
        result = await handle_inventory_assignment(data, db)
        return {
            "status": "received",
            "event": event,
            "inventory_id": inventory_id,
            "customer_id": customer_id,
            "customer_name": customer_name,
            "mac_address": mac_address,
            "serial_number": serial_number,
            "endpoint_found": result.get("endpoint_found", False),
            "subscriber_created": result.get("subscriber_created", False),
            "action": "processed"
        }

    elif event == "inventory.unassigned":
        logger.info(f"Splynx inventory unassigned: {inventory_id} from customer")
        # CPE removed from customer
        result = await handle_inventory_unassignment(data, db)
        return {
            "status": "received",
            "event": event,
            "inventory_id": inventory_id,
            "mac_address": mac_address,
            "serial_number": serial_number,
            "action": "processed"
        }

    elif event == "inventory.status_changed":
        logger.info(f"Splynx inventory status changed: {inventory_id} -> {item_status}")
        return {
            "status": "received",
            "event": event,
            "inventory_id": inventory_id,
            "new_status": item_status,
            "action": "logged"
        }

    elif event == "inventory.deleted":
        logger.info(f"Splynx inventory deleted: {inventory_id}")
        return {
            "status": "received",
            "event": event,
            "inventory_id": inventory_id,
            "action": "logged"
        }

    return {"status": "ignored", "event": event}


async def process_inventory_update(data: dict, db: AsyncSession) -> dict:
    """Process inventory update - check if we can link to an endpoint."""
    mac_address = data.get("mac_address")
    serial_number = data.get("serial_number")

    if not mac_address and not serial_number:
        return {"endpoint_found": False, "reason": "no_identifiers"}

    # Try to find matching endpoint
    endpoint = await find_endpoint_by_identifiers(mac_address, serial_number, db)

    if endpoint:
        return {
            "endpoint_found": True,
            "endpoint_id": str(endpoint.id),
            "endpoint_mac": endpoint.mac_address,
            "device_id": str(endpoint.device_id)
        }

    return {"endpoint_found": False}


async def handle_inventory_assignment(data: dict, db: AsyncSession) -> dict:
    """Handle inventory being assigned to a customer - potential auto-provisioning."""
    mac_address = data.get("mac_address")
    serial_number = data.get("serial_number")
    customer_id = data.get("customer_id")
    customer_name = data.get("customer_name")

    if not mac_address and not serial_number:
        return {
            "endpoint_found": False,
            "subscriber_created": False,
            "reason": "no_identifiers"
        }

    # Find matching endpoint
    endpoint = await find_endpoint_by_identifiers(mac_address, serial_number, db)

    if not endpoint:
        logger.info(f"No endpoint found for inventory MAC:{mac_address} SN:{serial_number}")
        return {
            "endpoint_found": False,
            "subscriber_created": False,
            "reason": "endpoint_not_found"
        }

    logger.info(f"Found endpoint {endpoint.id} for inventory assignment to customer {customer_id}")

    # Check if subscriber already exists
    existing = await db.execute(
        select(Subscriber).where(Subscriber.endpoint_id == endpoint.id)
    )
    existing_subscriber = existing.scalar_one_or_none()

    if existing_subscriber:
        # Update existing subscriber with Splynx customer info
        existing_subscriber.splynx_customer_id = customer_id
        existing_subscriber.name = customer_name or existing_subscriber.name
        existing_subscriber.updated_at = datetime.utcnow()
        await db.commit()

        logger.info(f"Updated existing subscriber {existing_subscriber.id} with Splynx customer {customer_id}")
        return {
            "endpoint_found": True,
            "endpoint_id": str(endpoint.id),
            "subscriber_created": False,
            "subscriber_updated": True,
            "subscriber_id": str(existing_subscriber.id)
        }

    # For now, don't auto-create subscribers - just log the match
    # This could be enabled via a setting
    logger.info(f"Endpoint {endpoint.id} ready for provisioning to customer {customer_id}")
    return {
        "endpoint_found": True,
        "endpoint_id": str(endpoint.id),
        "device_id": str(endpoint.device_id),
        "subscriber_created": False,
        "reason": "auto_provision_disabled"
    }


async def handle_inventory_unassignment(data: dict, db: AsyncSession) -> dict:
    """Handle inventory being unassigned from a customer."""
    mac_address = data.get("mac_address")
    serial_number = data.get("serial_number")

    endpoint = await find_endpoint_by_identifiers(mac_address, serial_number, db)

    if not endpoint:
        return {"endpoint_found": False}

    # Find subscriber and clear Splynx link
    result = await db.execute(
        select(Subscriber).where(Subscriber.endpoint_id == endpoint.id)
    )
    subscriber = result.scalar_one_or_none()

    if subscriber and subscriber.splynx_customer_id:
        subscriber.splynx_customer_id = None
        subscriber.updated_at = datetime.utcnow()
        await db.commit()
        logger.info(f"Cleared Splynx customer from subscriber {subscriber.id}")
        return {
            "endpoint_found": True,
            "subscriber_updated": True,
            "subscriber_id": str(subscriber.id)
        }

    return {"endpoint_found": True, "subscriber_updated": False}


async def find_endpoint_by_identifiers(
    mac_address: Optional[str],
    serial_number: Optional[str],
    db: AsyncSession
) -> Optional[Endpoint]:
    """Find an endpoint by MAC address or serial number."""
    conditions = []

    if mac_address:
        # Normalize MAC address formats
        mac_normalized = mac_address.upper().replace(":", "").replace("-", "")
        mac_with_colons = ":".join([mac_normalized[i:i+2] for i in range(0, 12, 2)]) if len(mac_normalized) == 12 else mac_address
        mac_with_dashes = "-".join([mac_normalized[i:i+2] for i in range(0, 12, 2)]) if len(mac_normalized) == 12 else mac_address

        conditions.extend([
            Endpoint.mac_address == mac_address,
            Endpoint.mac_address == mac_normalized,
            Endpoint.mac_address == mac_with_colons,
            Endpoint.mac_address == mac_with_dashes,
            Endpoint.mac_address == mac_address.lower(),
            Endpoint.mac_address == mac_address.upper(),
        ])

    if serial_number:
        conditions.append(Endpoint.serial_number == serial_number)

    if not conditions:
        return None

    result = await db.execute(
        select(Endpoint).where(or_(*conditions))
    )
    return result.scalar_one_or_none()


# ============================================================================
# Status and Configuration Endpoints
# ============================================================================

@router.get("/status")
async def splynx_status(db: AsyncSession = Depends(get_db)):
    """Get Splynx integration status."""
    api_url_result = await db.execute(
        select(Setting).where(Setting.key == "splynx_api_url")
    )
    api_url = api_url_result.scalar_one_or_none()

    api_key_result = await db.execute(
        select(Setting).where(Setting.key == "splynx_api_key")
    )
    api_key = api_key_result.scalar_one_or_none()

    webhook_secret_result = await db.execute(
        select(Setting).where(Setting.key == "splynx_webhook_secret")
    )
    webhook_secret = webhook_secret_result.scalar_one_or_none()

    auto_provision_result = await db.execute(
        select(Setting).where(Setting.key == "splynx_auto_provision")
    )
    auto_provision = auto_provision_result.scalar_one_or_none()

    return {
        "configured": bool(api_url and api_url.value and api_key and api_key.value),
        "api_url": api_url.value if api_url else None,
        "api_key_set": bool(api_key and api_key.value),
        "webhook_secret_set": bool(webhook_secret and webhook_secret.value),
        "auto_provision_enabled": auto_provision.value == "true" if auto_provision else False,
        "webhook_endpoint": "/api/splynx/webhook",
        "supported_events": [
            "customer.created", "customer.updated", "customer.deleted",
            "customer.blocked", "customer.activated",
            "service.created", "service.updated", "service.deleted",
            "service.activated", "service.suspended", "service.stopped",
            "inventory.created", "inventory.updated", "inventory.deleted",
            "inventory.assigned", "inventory.unassigned", "inventory.status_changed"
        ]
    }


@router.post("/test-connection")
async def test_splynx_connection(db: AsyncSession = Depends(get_db)):
    """Test connection to Splynx API using signature-based authentication."""
    try:
        client = await create_splynx_client_from_settings(db)
        if not client:
            return {"success": False, "error": "Splynx API not fully configured (need URL, API key, and API secret)"}

        result = await client.test_connection()
        await client.close()
        return result
    except Exception as e:
        return {
            "success": False,
            "error": f"Connection failed: {str(e)}"
        }


@router.get("/admins")
async def get_splynx_admins(db: AsyncSession = Depends(get_db)):
    """Get list of Splynx administrators for assignee dropdown."""
    try:
        client = await create_splynx_client_from_settings(db)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Splynx API not configured"
            )

        admins = await client.get_administrators()
        await client.close()

        return {
            "items": [
                {
                    "id": admin.id,
                    "name": admin.name,
                    "email": admin.email,
                    "role_name": admin.role_name,
                }
                for admin in admins
            ]
        }
    except SplynxApiError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Splynx API error: {e.message}"
        )


@router.post("/lookup/{endpoint_id}")
async def lookup_endpoint_in_splynx(
    endpoint_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Look up an endpoint's MAC address in Splynx inventory.

    Returns customer info if found.
    """
    # Get the endpoint
    result = await db.execute(
        select(Endpoint).where(Endpoint.id == endpoint_id)
    )
    endpoint = result.scalar_one_or_none()

    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not found"
        )

    if not endpoint.mac_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Endpoint has no MAC address"
        )

    # Get Splynx client
    try:
        client = await create_splynx_client_from_settings(db)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Splynx API not configured"
            )

        # Search inventory by MAC
        inventory_item = await client.search_inventory_by_mac(endpoint.mac_address)

        if not inventory_item:
            await client.close()
            return {
                "found": False,
                "mac_address": endpoint.mac_address,
                "message": "No inventory item found in Splynx for this MAC address"
            }

        # Get customer details if assigned
        customer = None
        services = []
        if inventory_item.customer_id:
            customer = await client.get_customer(inventory_item.customer_id)
            services = await client.get_customer_services(inventory_item.customer_id)

        await client.close()

        return {
            "found": True,
            "mac_address": endpoint.mac_address,
            "inventory": {
                "id": inventory_item.id,
                "name": inventory_item.name,
                "mac": inventory_item.mac,
                "serial_number": inventory_item.serial_number,
                "status": inventory_item.status,
                "vendor": inventory_item.vendor,
                "model": inventory_item.model,
            },
            "customer": {
                "id": customer.id,
                "name": customer.name,
                "email": customer.email,
                "phone": customer.phone,
                "status": customer.status,
                "address": f"{customer.street_1 or ''}, {customer.city or ''} {customer.zip_code or ''}".strip(", "),
            } if customer else None,
            "services": [
                {
                    "id": svc.id,
                    "description": svc.description,
                    "status": svc.status,
                    "tariff_name": svc.tariff_name,
                    "download_speed": svc.download_speed,
                    "upload_speed": svc.upload_speed,
                }
                for svc in services
            ]
        }

    except SplynxApiError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Splynx API error: {e.message}"
        )


@router.get("/webhook-log")
async def get_webhook_log(
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get recent webhook activity (placeholder - would need a log table)."""
    return {
        "message": "Webhook logging not yet implemented",
        "hint": "Check application logs for webhook activity"
    }


@router.post("/reconciliation/run")
async def trigger_reconciliation(db: AsyncSession = Depends(get_db)):
    """Manually trigger a reconciliation between GAM and Splynx."""
    from app.services.splynx_reconciliation import run_reconciliation
    import asyncio

    # Run reconciliation in background
    asyncio.create_task(run_reconciliation())

    return {
        "status": "started",
        "message": "Reconciliation started in background. Check logs for results."
    }


@router.get("/lookup-tasks")
async def get_lookup_tasks(
    status: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get list of Splynx lookup tasks."""
    from app.models import SplynxLookupTask

    query = select(SplynxLookupTask)
    if status:
        query = query.where(SplynxLookupTask.status == status)
    query = query.order_by(SplynxLookupTask.created_at.desc()).limit(limit)

    result = await db.execute(query)
    tasks = result.scalars().all()

    return {
        "items": [
            {
                "id": str(task.id),
                "endpoint_id": str(task.endpoint_id),
                "mac_address": task.mac_address,
                "status": task.status,
                "attempts": task.attempts,
                "last_attempt_at": task.last_attempt_at.isoformat() if task.last_attempt_at else None,
                "found_customer_id": task.found_customer_id,
                "found_customer_name": task.found_customer_name,
                "error_message": task.error_message,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            }
            for task in tasks
        ],
        "total": len(tasks),
    }
