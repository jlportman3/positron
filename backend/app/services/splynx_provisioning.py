"""
Splynx provisioning service.

Background loop that continuously checks for unprovisioned endpoints,
looks them up in Splynx, and provisions via the existing subscriber create code.
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import async_session_maker
from app.models import Endpoint, Subscriber, Setting, Device, SplynxLookupTask
from app.integrations.splynx_client import SplynxClient

logger = logging.getLogger(__name__)

_running = False
_task: Optional[asyncio.Task] = None
SCAN_INTERVAL = 60


async def get_setting(db: AsyncSession, key: str, default: str = "") -> str:
    result = await db.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    return setting.value if setting and setting.value else default


async def create_splynx_client(db: AsyncSession) -> Optional[SplynxClient]:
    api_url = await get_setting(db, "splynx_api_url")
    api_key = await get_setting(db, "splynx_api_key")
    api_secret = await get_setting(db, "splynx_api_secret")
    if not all([api_url, api_key, api_secret]):
        return None
    return SplynxClient(base_url=api_url, api_key=api_key, api_secret=api_secret)


async def create_lookup_task_for_endpoint(db: AsyncSession, endpoint: Endpoint) -> SplynxLookupTask:
    task = SplynxLookupTask(
        endpoint_id=endpoint.id,
        mac_address=endpoint.mac_address,
        status="pending",
        attempts=0,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def find_unprovisioned_endpoints(db: AsyncSession) -> list[Endpoint]:
    """Find all alive endpoints with no subscriber."""
    subscriber_exists = (
        select(Subscriber.id)
        .where(
            and_(
                Subscriber.device_id == Endpoint.device_id,
                Subscriber.endpoint_mac_address == Endpoint.mac_address,
            )
        )
        .correlate(Endpoint)
        .exists()
    )
    result = await db.execute(
        select(Endpoint).where(
            and_(
                Endpoint.alive == True,
                ~subscriber_exists,
            )
        )
    )
    return list(result.scalars().all())


async def process_unprovisioned_endpoints():
    """Scan for unprovisioned endpoints, look up in Splynx, provision if matched."""
    async with async_session_maker() as db:
        auto_provision = await get_setting(db, "splynx_auto_provision", "false") == "true"
        if not auto_provision:
            return

        client = await create_splynx_client(db)
        if not client:
            logger.debug("Splynx not configured, skipping auto-provision scan")
            return

        try:
            endpoints = await find_unprovisioned_endpoints(db)
            if not endpoints:
                return

            logger.info(f"Found {len(endpoints)} unprovisioned endpoint(s), checking Splynx")

            for endpoint in endpoints:
                try:
                    await lookup_and_provision(db, client, endpoint)
                except Exception as e:
                    logger.error(f"Error processing endpoint {endpoint.mac_address}: {e}")

        except Exception as e:
            logger.error(f"Error in auto-provision scan: {e}")
        finally:
            await client.close()


async def lookup_and_provision(
    db: AsyncSession,
    client: SplynxClient,
    endpoint: Endpoint,
):
    """Look up endpoint MAC in Splynx. If found, call the existing provision code."""
    mac = endpoint.mac_address

    inventory = await client.search_inventory_by_mac(mac)
    if not inventory:
        logger.debug(f"No Splynx match for {mac}")
        return

    customer_id = inventory.customer_id
    if not customer_id:
        logger.debug(f"Inventory found but no customer_id for {mac}")
        return

    customer = await client.get_customer(customer_id)
    services = await client.get_customer_services(customer_id)

    customer_name = customer.name if customer else "Unknown"
    service_id = services[0].id if services else None

    # Build description from customer address and service plan
    desc_parts = []
    if customer:
        addr = " ".join(filter(None, [customer.street_1, customer.city, customer.zip_code]))
        if addr:
            desc_parts.append(addr)
    if services:
        plan = services[0].tariff_name or services[0].description
        if plan:
            desc_parts.append(plan)
    description = " | ".join(desc_parts) if desc_parts else ""

    logger.info(f"Splynx match for {mac}: customer={customer_name} (ID={customer_id})")

    # Use the exact same provisioning code path as the manual button
    from app.api.subscribers import create_subscriber_on_device, SubscriberDeviceCreate

    data = SubscriberDeviceCreate(
        device_id=endpoint.device_id,
        endpoint_mac_address=mac,
        name=f"{customer_id} {customer_name}",
        description=description,
        port_if_index=endpoint.detected_port_if_index or "NONE",
    )

    # Call the existing endpoint function directly, passing db and a fake user
    # We need to bypass the Depends() injection, so call the inner logic
    try:
        result = await _provision_subscriber(db, data)
        logger.info(f"Auto-provisioned {mac}: {result.get('message', 'OK')}")
    except Exception as e:
        logger.error(f"Auto-provision failed for {mac}: {e}")
        return

    # Post-provision: write Splynx note and create QC ticket
    try:
        note = f"""=== GAM Auto-Provisioning ===
Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
CPE MAC: {mac}
Device: {endpoint.device_id}
Status: Active
"""
        await client.add_customer_note(customer_id, note)
    except Exception as e:
        logger.error(f"Failed to add Splynx customer note: {e}")

    try:
        assignee_id = await get_setting(db, "splynx_qc_ticket_assignee_id")
        await client.create_ticket(
            subject=f"Install QC: {customer_name}",
            message=f"Auto-provisioned CPE {mac} for customer {customer_name} ({customer_id}).",
            customer_id=customer_id,
            assigned_to=int(assignee_id) if assignee_id else None,
            priority="medium",
        )
    except Exception as e:
        logger.error(f"Failed to create QC ticket: {e}")


async def _provision_subscriber(db: AsyncSession, data) -> dict:
    """Run the same provision logic as POST /subscribers/device/create, without HTTP deps."""
    from app.models import Device, Endpoint, Subscriber, Bandwidth, Setting
    from app.rpc.client import create_client_for_device, GamRpcError

    device_result = await db.execute(select(Device).where(Device.id == data.device_id))
    device = device_result.scalar_one_or_none()
    if not device or not device.ip_address:
        raise Exception("Device not found or has no IP address")

    endpoint_result = await db.execute(
        select(Endpoint).where(
            (Endpoint.device_id == data.device_id) &
            (Endpoint.mac_address.ilike(data.endpoint_mac_address))
        )
    )
    endpoint = endpoint_result.scalar_one_or_none()
    if not endpoint:
        raise Exception(f"Endpoint not found on device for {data.endpoint_mac_address}")

    # Unprovisioned endpoints won't have conf_endpoint_id yet — we'll get it from add_endpoint

    # Load defaults from settings (same as the API endpoint)
    vlan_id = data.vlan_id
    port2_vlan_id = data.port2_vlan_id
    trunk_mode = data.trunk_mode
    if vlan_id == 0:
        vlan_setting = await db.execute(select(Setting).where(Setting.key == "splynx_default_vlan"))
        s = vlan_setting.scalar_one_or_none()
        if s and s.value:
            try:
                vlan_id = int(s.value)
                if port2_vlan_id == 0:
                    port2_vlan_id = vlan_id
            except ValueError:
                pass
        trunk_mode = True

    poe_mode = data.poe_mode_ctrl
    if not poe_mode:
        poe_setting = await db.execute(select(Setting).where(Setting.key == "splynx_default_poe_mode"))
        s = poe_setting.scalar_one_or_none()
        if s and s.value in ("enable", "disable"):
            poe_mode = s.value
        else:
            poe_mode = "disable"

    bw_profile_uid = 0
    if data.bw_profile_id:
        bw_result = await db.execute(select(Bandwidth).where(Bandwidth.id == data.bw_profile_id))
        bw = bw_result.scalar_one_or_none()
        if bw and bw.uid:
            bw_profile_uid = bw.uid

    client = await create_client_for_device(device)
    try:
        # Step 1: Configure endpoint on device (by MAC), get conf_endpoint_id back
        ep_result = await client.add_endpoint(
            mac_address=endpoint.mac_address,
            name=data.name,
            description=data.description,
            port_if_index=endpoint.detected_port_if_index or "autoPort",
        )
        # Extract the new conf_endpoint_id from the response
        conf_ep_id = endpoint.conf_endpoint_id
        if isinstance(ep_result, dict):
            conf_ep_id = ep_result.get("ConfEndpointId", conf_ep_id)
        if not conf_ep_id:
            # Re-read from device
            eps = await client.get_endpoints_brief()
            for ep in eps:
                key = ep.get("key", "")
                val = ep.get("val", {}) if isinstance(ep, dict) else {}
                if key.upper() == endpoint.mac_address.upper() or val.get("MacAddress", "").upper() == endpoint.mac_address.upper():
                    conf_ep_id = val.get("ConfEndpointId", 0)
                    break
        if not conf_ep_id:
            raise Exception(f"add_endpoint succeeded but no ConfEndpointId returned for {endpoint.mac_address}")

        endpoint.conf_endpoint_id = conf_ep_id

        # Step 2: Add subscriber
        result = await client.add_subscriber(
            name=data.name,
            description=data.description,
            endpoint_id=conf_ep_id,
            bw_profile_uid=bw_profile_uid,
            vlan_id=vlan_id,
            vlan_is_tagged=data.vlan_is_tagged,
            remapped_vlan_id=data.remapped_vlan_id,
            port2_vlan_id=port2_vlan_id,
            trunk_mode=trunk_mode,
            port_if_index=data.port_if_index,
            double_tags=data.double_tags,
            nni_if_index=data.nni_if_index,
            outer_tag_vlan_id=data.outer_tag_vlan_id,
            poe_mode_ctrl=poe_mode,
        )

        await client.save_config()

        # Get json_id from device
        json_id = None
        try:
            subs = await client.get_subscribers()
            for s in subs:
                val = s.get("val", {}) if isinstance(s, dict) else {}
                if val.get("Name") == data.name and val.get("EndpointId") == endpoint.conf_endpoint_id:
                    json_id = s.get("key") or val.get("Id")
                    break
        except Exception:
            pass

        await client.close()

        subscriber = Subscriber(
            device_id=device.id,
            name=data.name,
            description=data.description,
            json_id=json_id,
            endpoint_json_id=endpoint.conf_endpoint_id,
            endpoint_name=endpoint.conf_endpoint_name or endpoint.mac_address,
            endpoint_mac_address=endpoint.mac_address,
            bw_profile_name="",
            port1_vlan_id=str(vlan_id),
            vlan_is_tagged=data.vlan_is_tagged,
            trunk_mode=trunk_mode,
        )
        db.add(subscriber)

        endpoint.conf_user_name = data.name
        endpoint.conf_user_id = json_id
        endpoint.state = "ok"
        await db.commit()

        return {
            "status": "success",
            "message": f"Subscriber '{data.name}' created on device {device.serial_number}",
            "json_id": json_id,
        }
    except GamRpcError as e:
        raise Exception(f"RPC error: {e.message}")
    except Exception:
        await client.close()
        raise


async def background_lookup_loop():
    global _running
    logger.info("Starting Splynx auto-provision background task")
    while _running:
        try:
            await process_unprovisioned_endpoints()
        except Exception as e:
            logger.error(f"Error in auto-provision loop: {e}")
        await asyncio.sleep(SCAN_INTERVAL)
    logger.info("Splynx auto-provision background task stopped")


def start_background_task():
    global _running, _task
    if _running:
        return
    _running = True
    _task = asyncio.create_task(background_lookup_loop())
    logger.info("Splynx background task started")


def stop_background_task():
    global _running, _task
    _running = False
    if _task:
        _task.cancel()
        _task = None
    logger.info("Splynx background task stopped")
