"""
Endpoint management API.
"""
import logging
from typing import Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.deps import get_db, get_current_user, require_privilege
from app.models import User, Endpoint, Device, Subscriber
from app.schemas.endpoint import EndpointResponse, EndpointBrief, EndpointList
from app.rpc.client import GamRpcClient, GamRpcError, create_client_for_device


class EndpointConfigureRequest(BaseModel):
    """Request to configure/provision an endpoint."""
    port_if_index: str  # e.g., "G.hn 1/1", "G.hn 1/2"
    name: str = ""
    description: str = ""
    auto_port: bool = False

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=EndpointList)
async def list_endpoints(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    search: Optional[str] = None,
    device_id: Optional[UUID] = None,
    alive: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all endpoints with pagination and filtering."""
    query = select(Endpoint)

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Endpoint.mac_address.ilike(search_pattern)) |
            (Endpoint.conf_endpoint_name.ilike(search_pattern)) |
            (Endpoint.conf_user_name.ilike(search_pattern))
        )

    if device_id:
        query = query.where(Endpoint.device_id == device_id)

    if alive is not None:
        query = query.where(Endpoint.alive == alive)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get connected/disconnected counts
    connected_result = await db.execute(
        select(func.count()).where(Endpoint.alive == True)
    )
    connected_count = connected_result.scalar()

    disconnected_result = await db.execute(
        select(func.count()).where(Endpoint.alive == False)
    )
    disconnected_count = disconnected_result.scalar()

    # Apply pagination
    query = query.order_by(Endpoint.conf_endpoint_name, Endpoint.mac_address)
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    endpoints = result.scalars().all()

    items = [
        EndpointBrief(
            id=e.id,
            mac_address=e.mac_address,
            conf_endpoint_name=e.conf_endpoint_name,
            conf_endpoint_description=e.conf_endpoint_description,
            state=e.state,
            alive=e.alive,
            model_type=e.model_type,
            model_string=e.model_string,
            detected_port_if_index=e.detected_port_if_index,
            conf_port_if_index=e.conf_port_if_index,
            rx_phy_rate=e.rx_phy_rate,
            tx_phy_rate=e.tx_phy_rate,
            rx_max_xput=e.rx_max_xput,
            tx_max_xput=e.tx_max_xput,
            wire_length_feet=e.wire_length_feet,
            conf_user_name=e.conf_user_name,
            conf_bw_profile_name=e.conf_bw_profile_name,
            serial_number=e.serial_number,
            hw_product=e.hw_product,
            fw_version=e.fw_version,
            uptime=str(e.uptime_seconds) if e.uptime_seconds else None,
            port1_link=e.port1_link,
            port1_speed=e.port1_speed,
            port2_link=e.port2_link,
            port2_speed=e.port2_speed,
            device_id=e.device_id,
        )
        for e in endpoints
    ]

    return EndpointList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        connected_count=connected_count or 0,
        disconnected_count=disconnected_count or 0,
    )


@router.get("/{endpoint_id}", response_model=EndpointResponse)
async def get_endpoint(
    endpoint_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a single endpoint by ID."""
    result = await db.execute(
        select(Endpoint).where(Endpoint.id == endpoint_id)
    )
    endpoint = result.scalar_one_or_none()

    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not found",
        )

    return EndpointResponse(
        id=endpoint.id,
        device_id=endpoint.device_id,
        mac_address=endpoint.mac_address,
        conf_endpoint_id=endpoint.conf_endpoint_id,
        conf_endpoint_name=endpoint.conf_endpoint_name,
        conf_endpoint_description=endpoint.conf_endpoint_description,
        conf_port_if_index=endpoint.conf_port_if_index,
        conf_auto_port=endpoint.conf_auto_port,
        detected_port_if_index=endpoint.detected_port_if_index,
        conf_user_id=endpoint.conf_user_id,
        conf_user_name=endpoint.conf_user_name,
        conf_user_uid=endpoint.conf_user_uid,
        conf_bw_profile_id=endpoint.conf_bw_profile_id,
        conf_bw_profile_name=endpoint.conf_bw_profile_name,
        state=endpoint.state,
        state_code=endpoint.state_code,
        custom_state=endpoint.custom_state,
        alive=endpoint.alive,
        model_type=endpoint.model_type,
        model_string=endpoint.model_string,
        hw_product=endpoint.hw_product,
        device_name=endpoint.device_name,
        serial_number=endpoint.serial_number,
        fw_version=endpoint.fw_version,
        fw_mismatch=endpoint.fw_mismatch,
        mode=endpoint.mode,
        wire_length_meters=endpoint.wire_length_meters,
        wire_length_feet=endpoint.wire_length_feet,
        rx_phy_rate=endpoint.rx_phy_rate,
        tx_phy_rate=endpoint.tx_phy_rate,
        rx_alloc_bands=endpoint.rx_alloc_bands,
        tx_alloc_bands=endpoint.tx_alloc_bands,
        rx_max_xput=endpoint.rx_max_xput,
        tx_max_xput=endpoint.tx_max_xput,
        rx_usage=endpoint.rx_usage,
        tx_usage=endpoint.tx_usage,
        uptime=endpoint.uptime,
        port1_link=endpoint.port1_link,
        port1_speed=endpoint.port1_speed,
        port2_link=endpoint.port2_link,
        port2_speed=endpoint.port2_speed,
        created_at=endpoint.created_at,
        updated_at=endpoint.updated_at,
        last_details_update=endpoint.last_details_update,
    )


@router.post("/{endpoint_id}/poe-reset")
async def reset_endpoint_poe(
    endpoint_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(3)),  # Operator level
):
    """Reset PoE power for an endpoint.

    Cycles the PoE power, which can help with CPE connectivity issues.
    """
    result = await db.execute(
        select(Endpoint).where(Endpoint.id == endpoint_id)
    )
    endpoint = result.scalar_one_or_none()

    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not found",
        )

    if not endpoint.conf_endpoint_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Endpoint has no configured ID (not provisioned)",
        )

    # Get the device
    device_result = await db.execute(
        select(Device).where(Device.id == endpoint.device_id)
    )
    device = device_result.scalar_one_or_none()

    if not device or not device.ip_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device not found or has no IP address",
        )

    try:
        client = await create_client_for_device(device)
        result = await client.reset_endpoint_poe(endpoint.conf_endpoint_id)
        await client.close()

        return {
            "status": "success",
            "message": f"PoE reset initiated for endpoint {endpoint.mac_address}",
            "result": result,
        }
    except GamRpcError as e:
        logger.error(f"RPC error resetting PoE for endpoint {endpoint.mac_address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RPC error: {e.message}",
        )
    except Exception as e:
        logger.error(f"Error resetting PoE for endpoint {endpoint.mac_address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/{endpoint_id}/reboot")
async def reboot_endpoint(
    endpoint_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(3)),  # Operator level
):
    """Reboot an endpoint (CPE device).

    This will reboot the CPE device. It may take a few minutes to come back online.
    """
    result = await db.execute(
        select(Endpoint).where(Endpoint.id == endpoint_id)
    )
    endpoint = result.scalar_one_or_none()

    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not found",
        )

    if not endpoint.conf_endpoint_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Endpoint has no configured ID (not provisioned)",
        )

    # Get the device
    device_result = await db.execute(
        select(Device).where(Device.id == endpoint.device_id)
    )
    device = device_result.scalar_one_or_none()

    if not device or not device.ip_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device not found or has no IP address",
        )

    try:
        client = await create_client_for_device(device)
        result = await client.reboot_endpoint(endpoint.conf_endpoint_id)
        await client.close()

        return {
            "status": "success",
            "message": f"Reboot initiated for endpoint {endpoint.mac_address}",
            "result": result,
        }
    except GamRpcError as e:
        logger.error(f"RPC error rebooting endpoint {endpoint.mac_address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RPC error: {e.message}",
        )
    except Exception as e:
        logger.error(f"Error rebooting endpoint {endpoint.mac_address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/{endpoint_id}/configure")
async def configure_endpoint(
    endpoint_id: UUID,
    config: EndpointConfigureRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(3)),  # Operator level
):
    """Configure/provision an unconfigured endpoint.

    This assigns the endpoint to a specific G.hn port, taking it out of
    quarantine and making it available for subscriber creation.

    The endpoint must be in quarantined state (no conf_endpoint_id).
    After configuration, the endpoint will have a conf_endpoint_id and
    can be used to create subscribers.
    """
    result = await db.execute(
        select(Endpoint).where(Endpoint.id == endpoint_id)
    )
    endpoint = result.scalar_one_or_none()

    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not found",
        )

    if endpoint.conf_endpoint_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Endpoint is already configured (ID: {endpoint.conf_endpoint_id}). Use edit instead.",
        )

    # Get the device
    device_result = await db.execute(
        select(Device).where(Device.id == endpoint.device_id)
    )
    device = device_result.scalar_one_or_none()

    if not device or not device.ip_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device not found or has no IP address",
        )

    if device.read_only:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device is read-only. Cannot modify configuration.",
        )

    try:
        client = await create_client_for_device(device)

        # Add the endpoint configuration to the device
        rpc_result = await client.add_endpoint(
            mac_address=endpoint.mac_address,
            port_if_index=config.port_if_index,
            name=config.name,
            description=config.description,
            auto_port=config.auto_port,
        )

        # Save the config to the device
        await client.save_config()

        # Query device to get the new conf_endpoint_id
        # The add_endpoint returns null on success, so we need to look it up
        new_conf_id = None
        try:
            endpoint_configs = await client.get_endpoint_config()
            # Find the endpoint by MAC address
            for ep_config in endpoint_configs:
                ep_val = ep_config.get("val", {})
                if ep_val.get("MacAddress") == endpoint.mac_address:
                    new_conf_id = ep_val.get("Id")
                    break
        except Exception as e:
            logger.warning(f"Could not query endpoint config for ID: {e}")

        await client.close()

        # Update local database with the new configuration
        endpoint.conf_endpoint_id = new_conf_id
        endpoint.conf_port_if_index = config.port_if_index
        endpoint.conf_endpoint_name = config.name
        endpoint.conf_endpoint_description = config.description
        endpoint.conf_auto_port = config.auto_port
        # Update state to "ok" since it's now configured (will be updated on next sync)
        endpoint.state = "ok"

        await db.commit()
        await db.refresh(endpoint)

        return {
            "status": "success",
            "message": f"Endpoint {endpoint.mac_address} configured on port {config.port_if_index}",
            "endpoint_id": str(endpoint.id),
            "conf_endpoint_id": endpoint.conf_endpoint_id,
        }
    except GamRpcError as e:
        logger.error(f"RPC error configuring endpoint {endpoint.mac_address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RPC error: {e.message}",
        )
    except Exception as e:
        logger.error(f"Error configuring endpoint {endpoint.mac_address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete("/{endpoint_id}/configure")
async def unconfigure_endpoint(
    endpoint_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(3)),  # Operator level
):
    """Remove endpoint configuration from the device.

    This deletes the endpoint configuration, returning it to quarantined state.
    Any associated subscriber must be deleted first.
    """
    result = await db.execute(
        select(Endpoint).where(Endpoint.id == endpoint_id)
    )
    endpoint = result.scalar_one_or_none()

    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not found",
        )

    if not endpoint.conf_endpoint_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Endpoint is not configured",
        )

    # Get the device
    device_result = await db.execute(
        select(Device).where(Device.id == endpoint.device_id)
    )
    device = device_result.scalar_one_or_none()

    if not device or not device.ip_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device not found or has no IP address",
        )

    if device.read_only:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device is read-only. Cannot modify configuration.",
        )

    try:
        client = await create_client_for_device(device)

        # Delete the endpoint configuration from the device
        rpc_result = await client.delete_endpoint(endpoint.conf_endpoint_id)

        # Save the config
        await client.save_config()
        await client.close()

        # Update local database
        old_conf_id = endpoint.conf_endpoint_id
        endpoint.conf_endpoint_id = None
        endpoint.conf_port_if_index = None
        endpoint.conf_endpoint_name = None
        endpoint.conf_endpoint_description = None
        endpoint.conf_auto_port = None

        await db.commit()

        return {
            "status": "success",
            "message": f"Endpoint {endpoint.mac_address} configuration removed",
            "old_conf_endpoint_id": old_conf_id,
            "result": rpc_result,
        }
    except GamRpcError as e:
        logger.error(f"RPC error unconfiguring endpoint {endpoint.mac_address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RPC error: {e.message}",
        )
    except Exception as e:
        logger.error(f"Error unconfiguring endpoint {endpoint.mac_address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/{endpoint_id}/refresh-details")
async def refresh_endpoint_details(
    endpoint_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Fetch detailed endpoint information from the GAM device.

    Calls ghnAgent.status.endpointByMac.detailed.get to retrieve:
    - Serial number, firmware version, hardware product
    - PHY rates, wire length, throughput
    - Ethernet port link status
    - Uptime
    """
    result = await db.execute(
        select(Endpoint).where(Endpoint.id == endpoint_id)
    )
    endpoint = result.scalar_one_or_none()

    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not found",
        )

    device_result = await db.execute(
        select(Device).where(Device.id == endpoint.device_id)
    )
    device = device_result.scalar_one_or_none()

    if not device or not device.ip_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device not found or has no IP address",
        )

    try:
        client = await create_client_for_device(device)

        # Fetch detailed endpoint data
        detailed = await client.get_endpoint_detailed(endpoint.mac_address)

        if detailed:
            # Response can be a list of key/val pairs or a single dict
            data = detailed
            if isinstance(detailed, list) and len(detailed) > 0:
                item = detailed[0]
                data = item.get("val", item) if isinstance(item, dict) and "key" in item else item

            def get(key, default=None):
                if isinstance(data, dict):
                    for k in [key, key[0].lower() + key[1:], key.lower()]:
                        if k in data:
                            return data[k]
                return default

            def get_int(key, default=None):
                val = get(key)
                if val is None:
                    return default
                try:
                    return int(val)
                except (ValueError, TypeError):
                    return default

            # Update endpoint fields from detailed response
            endpoint.hw_product = get("HwProduct") or endpoint.hw_product
            endpoint.device_name = get("DeviceName") or endpoint.device_name
            endpoint.serial_number = get("SerialNumber") or endpoint.serial_number
            endpoint.fw_version = get("FwVersion") or endpoint.fw_version
            endpoint.mode = get("Mode") or endpoint.mode
            endpoint.wire_length_meters = get_int("WireLengthMeters") or endpoint.wire_length_meters
            endpoint.wire_length_feet = get_int("WireLengthFeet") or endpoint.wire_length_feet
            endpoint.rx_phy_rate = get_int("RxPhyRate") or endpoint.rx_phy_rate
            endpoint.tx_phy_rate = get_int("TxPhyRate") or endpoint.tx_phy_rate
            endpoint.rx_alloc_bands = get("RxAllocBands") or endpoint.rx_alloc_bands
            endpoint.tx_alloc_bands = get("TxAllocBands") or endpoint.tx_alloc_bands
            endpoint.rx_max_xput = get_int("RxMaxXput") or endpoint.rx_max_xput
            endpoint.tx_max_xput = get_int("TxMaxXput") or endpoint.tx_max_xput
            endpoint.rx_usage = get_int("RxUsage") or endpoint.rx_usage
            endpoint.tx_usage = get_int("TxUsage") or endpoint.tx_usage
            endpoint.uptime = get("Uptime") or endpoint.uptime

            # Ethernet port status - fetched via separate RPC calls
            # ghnAgent.status.endpoint.link.get takes [confEndpointId, position]
            if endpoint.conf_endpoint_id is not None:
                for port_num in [1, 2]:
                    try:
                        link_data = await client.get_endpoint_link(endpoint.conf_endpoint_id, port_num)
                        if link_data and isinstance(link_data, dict):
                            valid = link_data.get("Valid", False)
                            link = link_data.get("Link", False)
                            fdx = link_data.get("Fdx", False)
                            speed_raw = str(link_data.get("Speed", "")).replace("speed", "")

                            # Build display string
                            if speed_raw == "undefined" or not valid:
                                display = "Disabled" if not valid else ""
                            elif not link:
                                display = "Down"
                            else:
                                display = f"{speed_raw}/{'Full' if fdx else 'Half'}"

                            if port_num == 1:
                                endpoint.port1_valid = valid
                                endpoint.port1_link = link
                                endpoint.port1_fdx = fdx
                                endpoint.port1_speed = speed_raw if speed_raw != "undefined" else None
                                endpoint.port1_display = display
                            else:
                                endpoint.port2_valid = valid
                                endpoint.port2_link = link
                                endpoint.port2_fdx = fdx
                                endpoint.port2_speed = speed_raw if speed_raw != "undefined" else None
                                endpoint.port2_display = display
                    except Exception as link_err:
                        logging.getLogger(__name__).debug(f"Could not fetch port {port_num} link for endpoint {endpoint.mac_address}: {link_err}")

            # State fields
            endpoint.state = get("State") or endpoint.state
            endpoint.state_code = get("StateCode") or endpoint.state_code
            alive = get("Alive")
            if alive is not None:
                endpoint.alive = bool(alive)

            endpoint.last_details_update = datetime.utcnow()
            endpoint.updated_at = datetime.utcnow()

        await db.commit()
        await client.close()

        # Re-read to return fresh data
        await db.refresh(endpoint)

        return EndpointResponse(
            id=endpoint.id,
            device_id=endpoint.device_id,
            mac_address=endpoint.mac_address,
            conf_endpoint_id=endpoint.conf_endpoint_id,
            conf_endpoint_name=endpoint.conf_endpoint_name,
            conf_endpoint_description=endpoint.conf_endpoint_description,
            conf_port_if_index=endpoint.conf_port_if_index,
            conf_auto_port=endpoint.conf_auto_port,
            detected_port_if_index=endpoint.detected_port_if_index,
            conf_user_id=endpoint.conf_user_id,
            conf_user_name=endpoint.conf_user_name,
            conf_user_uid=endpoint.conf_user_uid,
            conf_bw_profile_id=endpoint.conf_bw_profile_id,
            conf_bw_profile_name=endpoint.conf_bw_profile_name,
            state=endpoint.state,
            state_code=endpoint.state_code,
            custom_state=endpoint.custom_state,
            alive=endpoint.alive,
            model_type=endpoint.model_type,
            model_string=endpoint.model_string,
            hw_product=endpoint.hw_product,
            device_name=endpoint.device_name,
            serial_number=endpoint.serial_number,
            fw_version=endpoint.fw_version,
            fw_mismatch=endpoint.fw_mismatch,
            mode=endpoint.mode,
            wire_length_meters=endpoint.wire_length_meters,
            wire_length_feet=endpoint.wire_length_feet,
            rx_phy_rate=endpoint.rx_phy_rate,
            tx_phy_rate=endpoint.tx_phy_rate,
            rx_alloc_bands=endpoint.rx_alloc_bands,
            tx_alloc_bands=endpoint.tx_alloc_bands,
            rx_max_xput=endpoint.rx_max_xput,
            tx_max_xput=endpoint.tx_max_xput,
            rx_usage=endpoint.rx_usage,
            tx_usage=endpoint.tx_usage,
            uptime=endpoint.uptime,
            port1_link=endpoint.port1_link,
            port1_speed=endpoint.port1_speed,
            port2_link=endpoint.port2_link,
            port2_speed=endpoint.port2_speed,
            created_at=endpoint.created_at,
            updated_at=endpoint.updated_at,
            last_details_update=endpoint.last_details_update,
        )

    except GamRpcError as e:
        logger.error(f"RPC error refreshing details for {endpoint.mac_address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RPC error: {e.message}",
        )
    except Exception as e:
        logger.error(f"Error refreshing details for {endpoint.mac_address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/{endpoint_id}/quarantine")
async def quarantine_endpoint(
    endpoint_id: UUID,
    data: dict = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(3)),
):
    """Quarantine an endpoint."""
    result = await db.execute(select(Endpoint).where(Endpoint.id == endpoint_id))
    endpoint = result.scalar_one_or_none()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    endpoint.quarantined = True
    endpoint.quarantine_reason = (data or {}).get("reason", "Manually quarantined")
    await db.commit()

    return {"status": "success", "message": f"Endpoint {endpoint.mac_address} quarantined"}


@router.post("/{endpoint_id}/unquarantine")
async def unquarantine_endpoint(
    endpoint_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(3)),
):
    """Remove endpoint from quarantine."""
    result = await db.execute(select(Endpoint).where(Endpoint.id == endpoint_id))
    endpoint = result.scalar_one_or_none()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    endpoint.quarantined = False
    endpoint.quarantine_reason = None
    await db.commit()

    return {"status": "success", "message": f"Endpoint {endpoint.mac_address} unquarantined"}


@router.post("/{endpoint_id}/auto-configure")
async def auto_configure_endpoint(
    endpoint_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(3)),
):
    """Auto-configure an endpoint using its detected port.

    Uses the detected_port_if_index to automatically provision the endpoint.
    """
    result = await db.execute(select(Endpoint).where(Endpoint.id == endpoint_id))
    endpoint = result.scalar_one_or_none()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    if endpoint.conf_endpoint_id:
        raise HTTPException(status_code=400, detail="Endpoint is already configured")

    if not endpoint.detected_port_if_index:
        raise HTTPException(status_code=400, detail="No detected port available for auto-configure")

    device_result = await db.execute(select(Device).where(Device.id == endpoint.device_id))
    device = device_result.scalar_one_or_none()
    if not device or not device.ip_address:
        raise HTTPException(status_code=400, detail="Device not found or has no IP address")

    if device.read_only:
        raise HTTPException(status_code=403, detail="Device is read-only")

    try:
        client = await create_client_for_device(device)
        await client.add_endpoint(
            mac_address=endpoint.mac_address,
            port_if_index=endpoint.detected_port_if_index,
            name=endpoint.mac_address,
            auto_port=True,
        )
        await client.save_config()

        # Look up the new conf_endpoint_id
        new_conf_id = None
        try:
            endpoint_configs = await client.get_endpoint_config()
            for ep_config in endpoint_configs:
                ep_val = ep_config.get("val", {})
                if ep_val.get("MacAddress") == endpoint.mac_address:
                    new_conf_id = ep_val.get("Id")
                    break
        except Exception:
            pass

        await client.close()

        endpoint.conf_endpoint_id = new_conf_id
        endpoint.conf_port_if_index = endpoint.detected_port_if_index
        endpoint.conf_auto_port = True
        endpoint.quarantined = False
        endpoint.quarantine_reason = None
        endpoint.state = "ok"
        await db.commit()

        return {
            "status": "success",
            "message": f"Endpoint {endpoint.mac_address} auto-configured on {endpoint.detected_port_if_index}",
            "conf_endpoint_id": new_conf_id,
        }
    except GamRpcError as e:
        raise HTTPException(status_code=500, detail=f"RPC error: {e.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{endpoint_id}/unprovision")
async def unprovision_endpoint(
    endpoint_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(3)),  # Operator level
):
    """Unprovision an endpoint: remove subscriber and endpoint config from GAM.

    Steps:
    1. Find subscriber associated with this endpoint
    2. Delete subscriber from device via RPC
    3. Delete endpoint configuration from device via RPC
    4. Save device config
    5. Remove subscriber from database
    6. Clear endpoint provisioning fields (returns to quarantine/virgin state)
    """
    result = await db.execute(
        select(Endpoint).where(Endpoint.id == endpoint_id)
    )
    endpoint = result.scalar_one_or_none()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    # Find subscriber by endpoint MAC
    sub_result = await db.execute(
        select(Subscriber).where(
            (Subscriber.device_id == endpoint.device_id) &
            (Subscriber.endpoint_mac_address.ilike(endpoint.mac_address))
        )
    )
    subscriber = sub_result.scalar_one_or_none()

    # Get device
    dev_result = await db.execute(
        select(Device).where(Device.id == endpoint.device_id)
    )
    device = dev_result.scalar_one_or_none()
    if not device or not device.ip_address:
        raise HTTPException(status_code=400, detail="Device not found or has no IP address")

    try:
        client = await create_client_for_device(device)

        # Step 1: Delete subscriber from device
        if subscriber and subscriber.json_id:
            await client.delete_subscriber(subscriber.json_id)
        elif endpoint.conf_user_id:
            await client.delete_subscriber(endpoint.conf_user_id)

        # Step 2: Delete endpoint configuration from device
        if endpoint.conf_endpoint_id:
            await client.delete_endpoint(endpoint.conf_endpoint_id)

        await client.save_config()
        await client.close()
    except GamRpcError as e:
        raise HTTPException(status_code=500, detail=f"RPC error: {e.message}")

    # Clean up database
    if subscriber:
        await db.delete(subscriber)

    # Clear all provisioning fields - return to virgin/quarantine state
    endpoint.conf_user_name = None
    endpoint.conf_user_id = None
    endpoint.conf_bw_profile_id = None
    endpoint.conf_bw_profile_name = None
    endpoint.conf_endpoint_id = None
    endpoint.conf_endpoint_name = None
    endpoint.conf_port_if_index = None
    endpoint.conf_auto_port = False
    endpoint.state = "quarantine"
    await db.commit()

    return {"status": "success", "message": f"Endpoint {endpoint.mac_address} unprovisioned"}
