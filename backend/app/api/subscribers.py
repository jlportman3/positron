"""
Subscriber management API.
"""
import logging
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.deps import get_db, get_current_user, require_privilege
from app.models import User, Subscriber, Device, Endpoint, Bandwidth, Setting
from app.schemas.subscriber import (
    SubscriberCreate,
    SubscriberUpdate,
    SubscriberResponse,
    SubscriberList,
)
from app.rpc.client import GamRpcClient, GamRpcError, create_client_for_device

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=SubscriberList)
async def list_subscribers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    search: Optional[str] = None,
    device_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all subscribers with pagination and filtering."""
    query = select(Subscriber)

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Subscriber.name.ilike(search_pattern)) |
            (Subscriber.endpoint_mac_address.ilike(search_pattern)) |
            (Subscriber.description.ilike(search_pattern))
        )

    if device_id:
        query = query.where(Subscriber.device_id == device_id)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    query = query.order_by(Subscriber.name)
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    subscribers = result.scalars().all()

    items = [
        SubscriberResponse(
            id=s.id,
            device_id=s.device_id,
            endpoint_id=s.endpoint_id,
            json_id=s.json_id,
            uid=s.uid,
            name=s.name,
            description=s.description,
            endpoint_json_id=s.endpoint_json_id,
            endpoint_name=s.endpoint_name,
            endpoint_mac_address=s.endpoint_mac_address,
            bw_profile_id=s.bw_profile_id,
            bw_profile_name=s.bw_profile_name,
            bw_profile_uid=s.bw_profile_uid,
            port1_vlan_id=s.port1_vlan_id,
            vlan_is_tagged=s.vlan_is_tagged,
            allowed_tagged_vlan=s.allowed_tagged_vlan,
            port2_vlan_id=s.port2_vlan_id,
            vlan_is_tagged2=s.vlan_is_tagged2,
            allowed_tagged_vlan2=s.allowed_tagged_vlan2,
            remapped_vlan_id=s.remapped_vlan_id,
            double_tags=s.double_tags,
            trunk_mode=s.trunk_mode,
            port_if_index=s.port_if_index,
            nni_if_index=s.nni_if_index,
            poe_mode_ctrl=s.poe_mode_ctrl,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in subscribers
    ]

    return SubscriberList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{subscriber_id}", response_model=SubscriberResponse)
async def get_subscriber(
    subscriber_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a single subscriber by ID."""
    result = await db.execute(
        select(Subscriber).where(Subscriber.id == subscriber_id)
    )
    subscriber = result.scalar_one_or_none()

    if not subscriber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscriber not found",
        )

    return SubscriberResponse(
        id=subscriber.id,
        device_id=subscriber.device_id,
        endpoint_id=subscriber.endpoint_id,
        json_id=subscriber.json_id,
        uid=subscriber.uid,
        name=subscriber.name,
        description=subscriber.description,
        endpoint_json_id=subscriber.endpoint_json_id,
        endpoint_name=subscriber.endpoint_name,
        endpoint_mac_address=subscriber.endpoint_mac_address,
        bw_profile_id=subscriber.bw_profile_id,
        bw_profile_name=subscriber.bw_profile_name,
        bw_profile_uid=subscriber.bw_profile_uid,
        port1_vlan_id=subscriber.port1_vlan_id,
        vlan_is_tagged=subscriber.vlan_is_tagged,
        allowed_tagged_vlan=subscriber.allowed_tagged_vlan,
        port2_vlan_id=subscriber.port2_vlan_id,
        vlan_is_tagged2=subscriber.vlan_is_tagged2,
        allowed_tagged_vlan2=subscriber.allowed_tagged_vlan2,
        remapped_vlan_id=subscriber.remapped_vlan_id,
        double_tags=subscriber.double_tags,
        trunk_mode=subscriber.trunk_mode,
        port_if_index=subscriber.port_if_index,
        nni_if_index=subscriber.nni_if_index,
        poe_mode_ctrl=subscriber.poe_mode_ctrl,
        created_at=subscriber.created_at,
        updated_at=subscriber.updated_at,
    )


@router.post("", response_model=SubscriberResponse, status_code=status.HTTP_201_CREATED)
async def create_subscriber(
    subscriber_data: SubscriberCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(3)),  # Operator level
):
    """Create a new subscriber in the database.

    Note: This does NOT create the subscriber on the device yet.
    Use the device sync or JSON-RPC service for that.
    """
    # Verify device exists
    device_result = await db.execute(
        select(Device).where(Device.id == subscriber_data.device_id)
    )
    if not device_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    # If endpoint MAC provided, find and link endpoint
    endpoint_id = None
    if subscriber_data.endpoint_mac_address:
        endpoint_result = await db.execute(
            select(Endpoint).where(
                Endpoint.mac_address == subscriber_data.endpoint_mac_address
            )
        )
        endpoint = endpoint_result.scalar_one_or_none()
        if endpoint:
            endpoint_id = endpoint.id

    subscriber = Subscriber(
        device_id=subscriber_data.device_id,
        endpoint_id=endpoint_id,
        name=subscriber_data.name,
        description=subscriber_data.description,
        endpoint_mac_address=subscriber_data.endpoint_mac_address,
        bw_profile_id=subscriber_data.bw_profile_id,
        port1_vlan_id=subscriber_data.port1_vlan_id,
        vlan_is_tagged=subscriber_data.vlan_is_tagged,
        allowed_tagged_vlan=subscriber_data.allowed_tagged_vlan,
        port2_vlan_id=subscriber_data.port2_vlan_id,
        vlan_is_tagged2=subscriber_data.vlan_is_tagged2,
        allowed_tagged_vlan2=subscriber_data.allowed_tagged_vlan2,
        remapped_vlan_id=subscriber_data.remapped_vlan_id,
        double_tags=subscriber_data.double_tags,
        trunk_mode=subscriber_data.trunk_mode,
        port_if_index=subscriber_data.port_if_index,
        nni_if_index=subscriber_data.nni_if_index,
        poe_mode_ctrl=subscriber_data.poe_mode_ctrl,
    )
    db.add(subscriber)
    await db.commit()
    await db.refresh(subscriber)

    return SubscriberResponse(
        id=subscriber.id,
        device_id=subscriber.device_id,
        endpoint_id=subscriber.endpoint_id,
        json_id=subscriber.json_id,
        uid=subscriber.uid,
        name=subscriber.name,
        description=subscriber.description,
        endpoint_json_id=subscriber.endpoint_json_id,
        endpoint_name=subscriber.endpoint_name,
        endpoint_mac_address=subscriber.endpoint_mac_address,
        bw_profile_id=subscriber.bw_profile_id,
        bw_profile_name=subscriber.bw_profile_name,
        bw_profile_uid=subscriber.bw_profile_uid,
        port1_vlan_id=subscriber.port1_vlan_id,
        vlan_is_tagged=subscriber.vlan_is_tagged,
        allowed_tagged_vlan=subscriber.allowed_tagged_vlan,
        port2_vlan_id=subscriber.port2_vlan_id,
        vlan_is_tagged2=subscriber.vlan_is_tagged2,
        allowed_tagged_vlan2=subscriber.allowed_tagged_vlan2,
        remapped_vlan_id=subscriber.remapped_vlan_id,
        double_tags=subscriber.double_tags,
        trunk_mode=subscriber.trunk_mode,
        port_if_index=subscriber.port_if_index,
        nni_if_index=subscriber.nni_if_index,
        poe_mode_ctrl=subscriber.poe_mode_ctrl,
        created_at=subscriber.created_at,
        updated_at=subscriber.updated_at,
    )


@router.patch("/{subscriber_id}", response_model=SubscriberResponse)
async def update_subscriber(
    subscriber_id: UUID,
    subscriber_data: SubscriberUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(3)),  # Operator level
):
    """Update a subscriber."""
    result = await db.execute(
        select(Subscriber).where(Subscriber.id == subscriber_id)
    )
    subscriber = result.scalar_one_or_none()

    if not subscriber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscriber not found",
        )

    update_data = subscriber_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(subscriber, field, value)

    await db.commit()
    await db.refresh(subscriber)

    return SubscriberResponse(
        id=subscriber.id,
        device_id=subscriber.device_id,
        endpoint_id=subscriber.endpoint_id,
        json_id=subscriber.json_id,
        uid=subscriber.uid,
        name=subscriber.name,
        description=subscriber.description,
        endpoint_json_id=subscriber.endpoint_json_id,
        endpoint_name=subscriber.endpoint_name,
        endpoint_mac_address=subscriber.endpoint_mac_address,
        bw_profile_id=subscriber.bw_profile_id,
        bw_profile_name=subscriber.bw_profile_name,
        bw_profile_uid=subscriber.bw_profile_uid,
        port1_vlan_id=subscriber.port1_vlan_id,
        vlan_is_tagged=subscriber.vlan_is_tagged,
        allowed_tagged_vlan=subscriber.allowed_tagged_vlan,
        port2_vlan_id=subscriber.port2_vlan_id,
        vlan_is_tagged2=subscriber.vlan_is_tagged2,
        allowed_tagged_vlan2=subscriber.allowed_tagged_vlan2,
        remapped_vlan_id=subscriber.remapped_vlan_id,
        double_tags=subscriber.double_tags,
        trunk_mode=subscriber.trunk_mode,
        port_if_index=subscriber.port_if_index,
        nni_if_index=subscriber.nni_if_index,
        poe_mode_ctrl=subscriber.poe_mode_ctrl,
        created_at=subscriber.created_at,
        updated_at=subscriber.updated_at,
    )


@router.delete("/{subscriber_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscriber(
    subscriber_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(5)),  # Manager level
):
    """Delete a subscriber from the database.

    Note: This does NOT delete from the device.
    """
    result = await db.execute(
        select(Subscriber).where(Subscriber.id == subscriber_id)
    )
    subscriber = result.scalar_one_or_none()

    if not subscriber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscriber not found",
        )

    await db.delete(subscriber)
    await db.commit()


# Device push endpoints - these push changes to the actual device

class SubscriberDeviceCreate(BaseModel):
    """Create subscriber on device."""
    device_id: UUID
    endpoint_mac_address: str
    name: str
    description: str = ""
    bw_profile_id: Optional[UUID] = None
    vlan_id: int = 0
    vlan_is_tagged: bool = False
    remapped_vlan_id: int = 0
    port2_vlan_id: int = 0
    trunk_mode: bool = False
    port_if_index: str = "NONE"  # String: "NONE", "G.hn 1/1", etc.
    double_tags: bool = False
    nni_if_index: str = "NONE"  # String: "NONE", "Gi 1/1", "10G 1/1", etc.
    outer_tag_vlan_id: int = 0
    poe_mode_ctrl: str = ""


@router.post("/device/create")
async def create_subscriber_on_device(
    data: SubscriberDeviceCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(3)),  # Operator level
):
    """Create a subscriber on the device.

    This provisions a new subscriber directly on the GAM device and saves
    the config. Use this for new subscriber provisioning.
    """
    # Get device
    device_result = await db.execute(
        select(Device).where(Device.id == data.device_id)
    )
    device = device_result.scalar_one_or_none()

    if not device or not device.ip_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device not found or has no IP address",
        )

    # Find endpoint by MAC
    endpoint_result = await db.execute(
        select(Endpoint).where(
            (Endpoint.device_id == data.device_id) &
            (Endpoint.mac_address.ilike(data.endpoint_mac_address))
        )
    )
    endpoint = endpoint_result.scalar_one_or_none()

    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not found on this device",
        )

    if not endpoint.conf_endpoint_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Endpoint has no configured ID",
        )

    # Load default VLAN from settings if not provided
    vlan_id = data.vlan_id
    port2_vlan_id = data.port2_vlan_id
    trunk_mode = data.trunk_mode
    if vlan_id == 0:
        vlan_setting = await db.execute(
            select(Setting).where(Setting.key == "splynx_default_vlan")
        )
        s = vlan_setting.scalar_one_or_none()
        if s and s.value:
            try:
                vlan_id = int(s.value)
                # Apply same VLAN to port 2 if not explicitly set
                if port2_vlan_id == 0:
                    port2_vlan_id = vlan_id
            except ValueError:
                pass
        # Default trunk mode to True when using default VLAN
        trunk_mode = True

    # Load default PoE mode from settings if not provided
    poe_mode = data.poe_mode_ctrl
    if not poe_mode:
        poe_setting = await db.execute(
            select(Setting).where(Setting.key == "splynx_default_poe_mode")
        )
        s = poe_setting.scalar_one_or_none()
        if s and s.value in ("enable", "disable"):
            poe_mode = s.value

    # Get bandwidth profile UID
    bw_profile_uid = 0
    if data.bw_profile_id:
        bw_result = await db.execute(
            select(Bandwidth).where(Bandwidth.id == data.bw_profile_id)
        )
        bw = bw_result.scalar_one_or_none()
        if bw and bw.uid:
            bw_profile_uid = bw.uid

    try:
        client = await create_client_for_device(device)

        # Add subscriber
        result = await client.add_subscriber(
            name=data.name,
            description=data.description,
            endpoint_id=endpoint.conf_endpoint_id,
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

        # Save config
        await client.save_config()

        # Query device to get the new subscriber's json_id
        json_id = None
        try:
            subs = await client.get_subscribers()
            for s in subs:
                val = s.get("val", {}) if isinstance(s, dict) else {}
                if val.get("Name") == data.name and val.get("EndpointId") == endpoint.conf_endpoint_id:
                    json_id = s.get("key") or val.get("Id")
                    break
        except Exception:
            pass  # Non-critical - subscriber was created, just can't get ID

        await client.close()

        # Save subscriber record to database
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

        # Update endpoint provisioning fields
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
        logger.error(f"RPC error creating subscriber: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RPC error: {e.message}",
        )
    except Exception as e:
        logger.error(f"Error creating subscriber: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


class SubscriberDeviceUpdate(BaseModel):
    """Update subscriber on device."""
    name: str
    description: str = ""
    bw_profile_id: Optional[UUID] = None
    vlan_id: int = 0
    vlan_is_tagged: bool = False
    remapped_vlan_id: int = 0
    port2_vlan_id: int = 0
    port2_vlan_is_tagged: bool = False
    trunk_mode: bool = False
    port_if_index: str = "NONE"  # String: "NONE", "G.hn 1/1", etc.
    double_tags: bool = False
    nni_if_index: str = "NONE"  # String: "NONE", "Gi 1/1", "10G 1/1", etc.
    outer_tag_vlan_id: int = 0
    poe_mode_ctrl: str = ""


@router.put("/{subscriber_id}/device")
async def update_subscriber_on_device(
    subscriber_id: UUID,
    data: SubscriberDeviceUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(3)),  # Operator level
):
    """Update a subscriber on the device.

    This modifies an existing subscriber on the GAM device and saves the config.
    """
    # Get subscriber
    result = await db.execute(
        select(Subscriber).where(Subscriber.id == subscriber_id)
    )
    subscriber = result.scalar_one_or_none()

    if not subscriber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscriber not found",
        )

    if not subscriber.json_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subscriber has no device JSON ID (not synced from device)",
        )

    # Get device
    device_result = await db.execute(
        select(Device).where(Device.id == subscriber.device_id)
    )
    device = device_result.scalar_one_or_none()

    if not device or not device.ip_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device not found or has no IP address",
        )

    # Get endpoint ID for the subscriber
    endpoint_id = 0
    if subscriber.endpoint_id:
        endpoint_result = await db.execute(
            select(Endpoint).where(Endpoint.id == subscriber.endpoint_id)
        )
        endpoint = endpoint_result.scalar_one_or_none()
        if endpoint and endpoint.conf_endpoint_id:
            endpoint_id = endpoint.conf_endpoint_id

    # Get bandwidth profile UID
    bw_profile_uid = 0
    if data.bw_profile_id:
        bw_result = await db.execute(
            select(Bandwidth).where(Bandwidth.id == data.bw_profile_id)
        )
        bw = bw_result.scalar_one_or_none()
        if bw and bw.uid:
            bw_profile_uid = bw.uid

    try:
        client = await create_client_for_device(device)

        # Edit subscriber
        result = await client.edit_subscriber(
            json_id=subscriber.json_id,
            name=data.name,
            description=data.description,
            endpoint_id=endpoint_id,
            bw_profile_uid=bw_profile_uid,
            vlan_id=data.vlan_id,
            vlan_is_tagged=data.vlan_is_tagged,
            remapped_vlan_id=data.remapped_vlan_id,
            port2_vlan_id=data.port2_vlan_id,
            port2_vlan_is_tagged=data.port2_vlan_is_tagged,
            trunk_mode=data.trunk_mode,
            port_if_index=data.port_if_index,
            double_tags=data.double_tags,
            nni_if_index=data.nni_if_index,
            outer_tag_vlan_id=data.outer_tag_vlan_id,
            poe_mode_ctrl=data.poe_mode_ctrl,
        )

        # Save config
        await client.save_config()
        await client.close()

        # Update local database record
        subscriber.name = data.name
        subscriber.description = data.description
        # port1_vlan_id is a string field that stores formatted VLAN info
        subscriber.port1_vlan_id = str(data.vlan_id) if data.vlan_id else None
        subscriber.vlan_is_tagged = data.vlan_is_tagged
        subscriber.remapped_vlan_id = data.remapped_vlan_id
        subscriber.port2_vlan_id = str(data.port2_vlan_id) if data.port2_vlan_id else None
        subscriber.vlan_is_tagged2 = data.port2_vlan_is_tagged
        subscriber.trunk_mode = data.trunk_mode
        subscriber.port_if_index = data.port_if_index
        subscriber.double_tags = data.double_tags
        subscriber.nni_if_index = data.nni_if_index
        subscriber.poe_mode_ctrl = data.poe_mode_ctrl if data.poe_mode_ctrl else None
        if data.bw_profile_id:
            subscriber.bw_profile_id = data.bw_profile_id
        await db.commit()

        return {
            "status": "success",
            "message": f"Subscriber '{data.name}' updated on device {device.serial_number}",
            "result": result,
        }
    except GamRpcError as e:
        logger.error(f"RPC error updating subscriber: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RPC error: {e.message}",
        )
    except Exception as e:
        logger.error(f"Error updating subscriber: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete("/{subscriber_id}/device")
async def delete_subscriber_from_device(
    subscriber_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(5)),  # Manager level
):
    """Delete a subscriber from the device.

    This removes the subscriber from the GAM device and saves the config.
    The database record is also removed.
    """
    # Get subscriber
    result = await db.execute(
        select(Subscriber).where(Subscriber.id == subscriber_id)
    )
    subscriber = result.scalar_one_or_none()

    if not subscriber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscriber not found",
        )

    if not subscriber.json_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subscriber has no device JSON ID (not synced from device)",
        )

    # Get device
    device_result = await db.execute(
        select(Device).where(Device.id == subscriber.device_id)
    )
    device = device_result.scalar_one_or_none()

    if not device or not device.ip_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device not found or has no IP address",
        )

    try:
        client = await create_client_for_device(device)

        # Delete subscriber from device
        result = await client.delete_subscriber(subscriber.json_id)

        # Also delete the endpoint config to fully release it
        endpoint = None
        if subscriber.endpoint_mac_address:
            ep_result = await db.execute(
                select(Endpoint).where(
                    (Endpoint.device_id == subscriber.device_id) &
                    (Endpoint.mac_address.ilike(subscriber.endpoint_mac_address))
                )
            )
            endpoint = ep_result.scalar_one_or_none()

        if endpoint and endpoint.conf_endpoint_id:
            try:
                await client.delete_endpoint(endpoint.conf_endpoint_id)
            except GamRpcError:
                pass  # Non-critical — subscriber already deleted

        # Save config
        await client.save_config()
        await client.close()

        # Delete subscriber from database
        await db.delete(subscriber)

        # Release endpoint — clear provisioning fields, return to quarantine
        if endpoint:
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

        return {
            "status": "success",
            "message": f"Subscriber '{subscriber.name}' deleted and endpoint released",
        }
    except GamRpcError as e:
        logger.error(f"RPC error deleting subscriber: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RPC error: {e.message}",
        )
    except Exception as e:
        logger.error(f"Error deleting subscriber: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
