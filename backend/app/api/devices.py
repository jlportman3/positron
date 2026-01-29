"""
Device management API endpoints.
"""
import logging
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.deps import get_db, get_current_user, require_privilege
from app.models import Device, User, Endpoint, Subscriber, Alarm
from app.models.audit_log import AuditLog
from app.schemas.device import (
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
    DeviceBrief,
    DeviceList,
)
from app.services.device_sync import DeviceSyncService
from app.rpc.client import GamRpcClient, GamRpcError, create_client_for_device

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=DeviceList)
async def list_devices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    search: Optional[str] = None,
    is_online: Optional[bool] = None,
    group_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all devices with pagination and filtering."""
    # Base query
    query = select(Device)

    # Apply filters
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Device.serial_number.ilike(search_pattern)) |
            (Device.name.ilike(search_pattern)) |
            (Device.ip_address.ilike(search_pattern))
        )

    if is_online is not None:
        query = query.where(Device.is_online == is_online)

    if group_id:
        query = query.where(Device.group_id == group_id)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get online/offline counts
    online_result = await db.execute(
        select(func.count()).where(Device.is_online == True)
    )
    online_count = online_result.scalar()

    offline_result = await db.execute(
        select(func.count()).where(Device.is_online == False)
    )
    offline_count = offline_result.scalar()

    # Apply pagination
    query = query.order_by(Device.name, Device.serial_number)
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    devices = result.scalars().all()

    # Build response items with counts
    items = []
    for device in devices:
        # Get counts (could be optimized with subqueries)
        endpoint_count = await db.scalar(
            select(func.count()).where(Endpoint.device_id == device.id)
        )
        subscriber_count = await db.scalar(
            select(func.count()).where(Subscriber.device_id == device.id)
        )
        alarm_count = await db.scalar(
            select(func.count()).where(
                (Alarm.device_id == device.id) & (Alarm.closing_date == None)
            )
        )

        items.append(DeviceBrief(
            id=device.id,
            serial_number=device.serial_number,
            name=device.name,
            ip_address=device.ip_address,
            is_online=device.is_online,
            read_only=device.read_only,
            product_class=device.product_class,
            software_version=device.software_version,
            endpoint_count=endpoint_count or 0,
            subscriber_count=subscriber_count or 0,
            alarm_count=alarm_count or 0,
            uptime=device.uptime,
            last_seen=device.last_seen,
        ))

    return DeviceList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        online_count=online_count or 0,
        offline_count=offline_count or 0,
    )


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a single device by ID."""
    result = await db.execute(
        select(Device).where(Device.id == device_id)
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    # Get counts
    endpoint_count = await db.scalar(
        select(func.count()).where(Endpoint.device_id == device.id)
    )
    subscriber_count = await db.scalar(
        select(func.count()).where(Subscriber.device_id == device.id)
    )
    alarm_count = await db.scalar(
        select(func.count()).where(
            (Alarm.device_id == device.id) & (Alarm.closing_date == None)
        )
    )

    return DeviceResponse(
        id=device.id,
        serial_number=device.serial_number,
        mac_address=device.mac_address,
        name=device.name,
        vendor=device.vendor,
        product_class=device.product_class,
        hardware_version=device.hardware_version,
        compatible=device.compatible,
        uni_ports=device.uni_ports,
        clei_code=device.clei_code,
        ip_address=device.ip_address,
        fqdn=device.fqdn,
        proto=device.proto,
        port=device.port,
        software_version=device.software_version,
        software_revision=device.software_revision,
        software_build_date=device.software_build_date,
        firmware=device.firmware,
        swap_software_version=device.swap_software_version,
        swap_software_revision=device.swap_software_revision,
        swap_software_build_date=device.swap_software_build_date,
        rpc_username=device.rpc_username,
        is_virtual=device.is_virtual,
        is_online=device.is_online,
        read_only=device.read_only,
        uptime=device.uptime,
        location=device.location,
        contact=device.contact,
        group_id=device.group_id,
        created_at=device.created_at,
        updated_at=device.updated_at,
        last_announcement=device.last_announcement,
        last_seen=device.last_seen,
        endpoint_count=endpoint_count or 0,
        subscriber_count=subscriber_count or 0,
        alarm_count=alarm_count or 0,
    )


@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    device_data: DeviceCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(3)),  # Operator level
):
    """Manually create a device."""
    # Check for duplicate serial number
    existing = await db.execute(
        select(Device).where(Device.serial_number == device_data.serial_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Device with this serial number already exists",
        )

    device = Device(
        serial_number=device_data.serial_number,
        name=device_data.name,
        ip_address=device_data.ip_address,
        proto=device_data.proto,
        port=device_data.port,
        user_name=device_data.user_name,
        password=device_data.password,
        group_id=device_data.group_id,
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)

    return DeviceResponse(
        id=device.id,
        serial_number=device.serial_number,
        mac_address=device.mac_address,
        name=device.name,
        vendor=device.vendor,
        product_class=device.product_class,
        hardware_version=device.hardware_version,
        compatible=device.compatible,
        uni_ports=device.uni_ports,
        clei_code=device.clei_code,
        ip_address=device.ip_address,
        fqdn=device.fqdn,
        proto=device.proto,
        port=device.port,
        software_version=device.software_version,
        software_revision=device.software_revision,
        software_build_date=device.software_build_date,
        firmware=device.firmware,
        swap_software_version=device.swap_software_version,
        swap_software_revision=device.swap_software_revision,
        swap_software_build_date=device.swap_software_build_date,
        rpc_username=device.rpc_username,
        is_virtual=device.is_virtual,
        is_online=device.is_online,
        read_only=device.read_only,
        uptime=device.uptime,
        location=device.location,
        contact=device.contact,
        group_id=device.group_id,
        created_at=device.created_at,
        updated_at=device.updated_at,
        last_announcement=device.last_announcement,
        last_seen=device.last_seen,
        endpoint_count=0,
        subscriber_count=0,
        alarm_count=0,
    )


@router.patch("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: UUID,
    device_data: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(3)),  # Operator level
):
    """Update a device."""
    result = await db.execute(
        select(Device).where(Device.id == device_id)
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    # Update only provided fields
    update_data = device_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(device, field, value)

    await db.commit()
    await db.refresh(device)

    # Get counts
    endpoint_count = await db.scalar(
        select(func.count()).where(Endpoint.device_id == device.id)
    )
    subscriber_count = await db.scalar(
        select(func.count()).where(Subscriber.device_id == device.id)
    )
    alarm_count = await db.scalar(
        select(func.count()).where(
            (Alarm.device_id == device.id) & (Alarm.closing_date == None)
        )
    )

    return DeviceResponse(
        id=device.id,
        serial_number=device.serial_number,
        mac_address=device.mac_address,
        name=device.name,
        vendor=device.vendor,
        product_class=device.product_class,
        hardware_version=device.hardware_version,
        compatible=device.compatible,
        uni_ports=device.uni_ports,
        clei_code=device.clei_code,
        ip_address=device.ip_address,
        fqdn=device.fqdn,
        proto=device.proto,
        port=device.port,
        software_version=device.software_version,
        software_revision=device.software_revision,
        software_build_date=device.software_build_date,
        firmware=device.firmware,
        swap_software_version=device.swap_software_version,
        swap_software_revision=device.swap_software_revision,
        swap_software_build_date=device.swap_software_build_date,
        rpc_username=device.rpc_username,
        is_virtual=device.is_virtual,
        is_online=device.is_online,
        read_only=device.read_only,
        uptime=device.uptime,
        location=device.location,
        contact=device.contact,
        group_id=device.group_id,
        created_at=device.created_at,
        updated_at=device.updated_at,
        last_announcement=device.last_announcement,
        last_seen=device.last_seen,
        endpoint_count=endpoint_count or 0,
        subscriber_count=subscriber_count or 0,
        alarm_count=alarm_count or 0,
    )


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(7)),  # Admin level
):
    """Delete a device."""
    result = await db.execute(
        select(Device).where(Device.id == device_id)
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    await db.delete(device)
    await db.commit()


@router.post("/bulk-delete")
async def bulk_delete_devices(
    data: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(7)),  # Admin level
):
    """Bulk delete multiple devices. Only offline devices can be deleted."""
    device_ids = data.get("device_ids", [])
    if not device_ids:
        raise HTTPException(status_code=400, detail="No device IDs provided")

    results = []
    deleted = 0

    for did in device_ids:
        try:
            uid = UUID(str(did))
        except ValueError:
            results.append({"device_id": str(did), "status": "error", "detail": "Invalid UUID"})
            continue

        result = await db.execute(select(Device).where(Device.id == uid))
        device = result.scalar_one_or_none()
        if not device:
            results.append({"device_id": str(did), "status": "error", "detail": "Not found"})
            continue

        if device.is_online:
            results.append({
                "device_id": str(did),
                "serial_number": device.serial_number,
                "status": "skipped",
                "detail": "Device is online",
            })
            continue

        serial = device.serial_number
        await db.delete(device)
        deleted += 1
        results.append({
            "device_id": str(did),
            "serial_number": serial,
            "status": "deleted",
        })

    if deleted > 0:
        db.add(AuditLog(
            action="DELETE",
            entity_type="Device",
            username=user.username,
            description=f"Bulk deleted {deleted} device(s)",
        ))
        await db.commit()

    return {
        "message": f"Deleted {deleted}/{len(device_ids)} devices",
        "deleted": deleted,
        "results": results,
    }


@router.post("/{device_id}/sync")
async def sync_device(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(1)),  # At least Read access
):
    """Sync data from a device.

    Pulls endpoints, subscribers, bandwidth profiles, and port status
    from the device via JSON-RPC and stores them in the database.
    """
    result = await db.execute(
        select(Device).where(Device.id == device_id)
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    if not device.ip_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device has no IP address configured",
        )

    sync_service = DeviceSyncService(db)

    try:
        results = await sync_service.sync_device(device)
        return {
            "status": "success",
            "message": f"Synced device {device.serial_number}",
            "results": results,
        }
    except Exception as e:
        logger.error(f"Sync failed for device {device.serial_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}",
        )


@router.post("/sync-all")
async def sync_all_devices(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(3)),  # Operator level
):
    """Sync data from all online devices.

    Iterates through all online devices and syncs their data.
    """
    result = await db.execute(
        select(Device).where(Device.is_online == True)
    )
    devices = result.scalars().all()

    if not devices:
        return {
            "status": "success",
            "message": "No online devices to sync",
            "results": [],
        }

    sync_service = DeviceSyncService(db)
    results = []

    for device in devices:
        if not device.ip_address:
            results.append({
                "device_id": str(device.id),
                "serial_number": device.serial_number,
                "status": "skipped",
                "error": "No IP address",
            })
            continue

        try:
            sync_result = await sync_service.sync_device(device)
            sync_result["status"] = "success"
            results.append(sync_result)
        except Exception as e:
            logger.error(f"Sync failed for device {device.serial_number}: {e}")
            results.append({
                "device_id": str(device.id),
                "serial_number": device.serial_number,
                "status": "failed",
                "error": str(e),
            })

    success_count = sum(1 for r in results if r.get("status") == "success")
    return {
        "status": "success",
        "message": f"Synced {success_count}/{len(devices)} devices",
        "results": results,
    }


@router.post("/{device_id}/save-config")
async def save_device_config(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(3)),  # Operator level
):
    """Save running config to startup config on device.

    This persists all configuration changes to survive a reboot.
    """
    result = await db.execute(
        select(Device).where(Device.id == device_id)
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    if not device.ip_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device has no IP address configured",
        )

    try:
        client = await create_client_for_device(device)
        result = await client.save_config()
        await client.close()

        return {
            "status": "success",
            "message": f"Saved config on device {device.serial_number}",
            "result": result,
        }
    except GamRpcError as e:
        logger.error(f"RPC error saving config for device {device.serial_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RPC error: {e.message}",
        )
    except Exception as e:
        logger.error(f"Error saving config for device {device.serial_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/{device_id}/download-config")
async def download_device_config(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(3)),  # Operator level
):
    """Download device configuration.

    Returns the full device configuration as text.
    """
    result = await db.execute(
        select(Device).where(Device.id == device_id)
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    if not device.ip_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device has no IP address configured",
        )

    try:
        client = await create_client_for_device(device)
        config = await client.download_config()
        await client.close()

        return {
            "status": "success",
            "device_id": str(device.id),
            "serial_number": device.serial_number,
            "config": config,
        }
    except GamRpcError as e:
        logger.error(f"RPC error downloading config for device {device.serial_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RPC error: {e.message}",
        )
    except Exception as e:
        logger.error(f"Error downloading config for device {device.serial_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/{device_id}/firmware-swap")
async def swap_device_firmware(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(5)),  # Manager level
):
    """Swap to alternate firmware partition.

    Device will reboot to the other firmware partition.
    WARNING: This will cause a device reboot.
    """
    result = await db.execute(
        select(Device).where(Device.id == device_id)
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    if not device.ip_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device has no IP address configured",
        )

    try:
        client = await create_client_for_device(device)
        # Save config before swap
        await client.save_config()
        result = await client.firmware_swap()
        await client.close()

        return {
            "status": "success",
            "message": f"Firmware swap initiated on device {device.serial_number}. Device will reboot.",
            "result": result,
        }
    except GamRpcError as e:
        logger.error(f"RPC error swapping firmware for device {device.serial_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RPC error: {e.message}",
        )
    except Exception as e:
        logger.error(f"Error swapping firmware for device {device.serial_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# NTP/Timezone Configuration Endpoints

@router.get("/{device_id}/timezone")
async def get_device_timezone(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get timezone and NTP configuration from device via RPC."""
    result = await db.execute(
        select(Device).where(Device.id == device_id)
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    if not device.ip_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device has no IP address configured",
        )

    try:
        client = await create_client_for_device(device)

        timezone_data = None
        ntp_servers = None

        try:
            timezone_data = await client.get_timezone()
        except Exception as e:
            logger.warning(f"Failed to get timezone from {device.serial_number}: {e}")

        try:
            ntp_servers = await client.get_ntp_servers()
        except Exception as e:
            logger.warning(f"Failed to get NTP servers from {device.serial_number}: {e}")

        await client.close()

        return {
            "device_id": str(device.id),
            "serial_number": device.serial_number,
            "name": device.name or device.serial_number,
            "timezone": timezone_data,
            "ntp_servers": ntp_servers,
        }
    except Exception as e:
        logger.error(f"Error getting timezone for device {device.serial_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.patch("/{device_id}/timezone")
async def update_device_timezone(
    device_id: UUID,
    data: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(3)),
):
    """Update timezone and NTP configuration on device via RPC.

    Accepts:
        timezone: str - Timezone string e.g. "(UTC-06:00)"
        dst_enabled: bool - Enable daylight saving
        dst_start: str - DST start
        dst_end: str - DST end
        ntp_servers: list[str] - NTP server addresses
        ntp_enabled: bool - Enable/disable NTP
    """
    result = await db.execute(
        select(Device).where(Device.id == device_id)
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    if not device.ip_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device has no IP address configured",
        )

    try:
        client = await create_client_for_device(device)

        # Update timezone if provided
        if "timezone" in data:
            # Parse "(UTC-06:00)" format to offset minutes
            tz_str = data["timezone"]  # e.g., "(UTC-06:00)"
            offset_minutes = 0
            try:
                import re
                m = re.match(r'\(UTC([+-])(\d{2}):(\d{2})\)', tz_str)
                if m:
                    sign = -1 if m.group(1) == '-' else 1
                    offset_minutes = sign * (int(m.group(2)) * 60 + int(m.group(3)))
                elif tz_str == '(UTC00:00)':
                    offset_minutes = 0
            except Exception:
                pass

            summer_mode = "enable" if data.get("dst_enabled", False) else "disable"
            await client.set_timezone(
                offset_minutes=offset_minutes,
                summer_time_mode=summer_mode,
            )

        # Update NTP servers if provided
        if "ntp_servers" in data:
            servers = [s for s in data["ntp_servers"] if s]
            if servers:
                await client.set_ntp_servers(servers)

        # Enable/disable NTP if provided
        if "ntp_enabled" in data:
            await client.set_ntp_mode(enabled=data["ntp_enabled"])

        await client.save_config()
        await client.close()

        return {
            "status": "success",
            "message": f"Timezone/NTP settings updated on device {device.serial_number}",
        }
    except GamRpcError as e:
        logger.error(f"RPC error setting timezone for device {device.serial_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RPC error: {e.message}",
        )
    except Exception as e:
        logger.error(f"Error setting timezone for device {device.serial_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/{device_id}/ntp")
async def get_device_ntp(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get device NTP configuration."""
    result = await db.execute(
        select(Device).where(Device.id == device_id)
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    if not device.ip_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device has no IP address configured",
        )

    try:
        client = await create_client_for_device(device)
        ntp_servers = await client.get_ntp_servers()
        await client.close()

        return {
            "device_id": str(device.id),
            "serial_number": device.serial_number,
            "ntp_servers": ntp_servers,
        }
    except GamRpcError as e:
        logger.error(f"RPC error getting NTP for device {device.serial_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RPC error: {e.message}",
        )
    except Exception as e:
        logger.error(f"Error getting NTP for device {device.serial_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/{device_id}/ntp")
async def set_device_ntp(
    device_id: UUID,
    servers: list[str],
    enabled: bool = True,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(3)),  # Operator level
):
    """Set device NTP configuration.

    Args:
        servers: List of NTP server addresses
        enabled: Enable/disable NTP
    """
    result = await db.execute(
        select(Device).where(Device.id == device_id)
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    if not device.ip_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device has no IP address configured",
        )

    try:
        client = await create_client_for_device(device)

        # Set NTP mode (enable/disable)
        await client.set_ntp_mode(enabled=enabled)

        # Set NTP servers
        if servers:
            await client.set_ntp_servers(servers)

        await client.save_config()
        await client.close()

        return {
            "status": "success",
            "message": f"NTP configuration set on device {device.serial_number}",
            "servers": servers,
            "enabled": enabled,
        }
    except GamRpcError as e:
        logger.error(f"RPC error setting NTP for device {device.serial_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RPC error: {e.message}",
        )
    except Exception as e:
        logger.error(f"Error setting NTP for device {device.serial_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# Discovery/Announcement Configuration Endpoints

@router.get("/{device_id}/discovery")
async def get_device_discovery(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get device discovery/announcement configuration."""
    result = await db.execute(
        select(Device).where(Device.id == device_id)
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    if not device.ip_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device has no IP address configured",
        )

    try:
        client = await create_client_for_device(device)
        discovery_config = await client.get_discovery_config()
        global_config = await client.get_discovery_global()
        await client.close()

        return {
            "device_id": str(device.id),
            "serial_number": device.serial_number,
            "discovery_target": discovery_config,
            "global_settings": global_config,
        }
    except GamRpcError as e:
        logger.error(f"RPC error getting discovery for device {device.serial_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RPC error: {e.message}",
        )
    except Exception as e:
        logger.error(f"Error getting discovery for device {device.serial_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/{device_id}/discovery")
async def set_device_discovery(
    device_id: UUID,
    url: str,
    username: str = "device",
    password: str = "device",
    period: int = 60,
    enabled: bool = True,
    use_ssl: bool = True,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(5)),  # Manager level
):
    """Set device discovery/announcement configuration.

    This configures where the device sends its periodic announcements.

    Args:
        url: Server URL to announce to (e.g., "https://alamo-gam.example.com:8000")
        username: HTTP Basic Auth username for announcements
        password: HTTP Basic Auth password for announcements
        period: Announcement period in seconds (default 60)
        enabled: Enable/disable discovery agent
        use_ssl: Use SSL for announcements
    """
    result = await db.execute(
        select(Device).where(Device.id == device_id)
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    if not device.ip_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device has no IP address configured",
        )

    try:
        client = await create_client_for_device(device)

        # Set global discovery settings
        await client.set_discovery_global(enabled=enabled, use_ssl=use_ssl)

        # Set discovery target URL
        await client.set_discovery_target(
            url=url,
            username=username,
            password=password,
            period=period,
        )

        await client.save_config()
        await client.close()

        return {
            "status": "success",
            "message": f"Discovery configuration set on device {device.serial_number}",
            "url": url,
            "period": period,
            "enabled": enabled,
        }
    except GamRpcError as e:
        logger.error(f"RPC error setting discovery for device {device.serial_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RPC error: {e.message}",
        )
    except Exception as e:
        logger.error(f"Error setting discovery for device {device.serial_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# Diagnostics Endpoints

@router.get("/{device_id}/signal-measurement")
async def get_device_signal_measurement(
    device_id: UUID,
    port_if_index: str = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get signal/spectrum measurement from device.

    Args:
        port_if_index: Optional specific port to measure (e.g., "G.hn 1/1")
    """
    result = await db.execute(
        select(Device).where(Device.id == device_id)
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    if not device.ip_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device has no IP address configured",
        )

    try:
        client = await create_client_for_device(device)
        measurement = await client.get_signal_measurement(port_if_index=port_if_index)
        await client.close()

        return {
            "device_id": str(device.id),
            "serial_number": device.serial_number,
            "port_if_index": port_if_index,
            "measurement": measurement,
        }
    except GamRpcError as e:
        logger.error(f"RPC error getting signal measurement for device {device.serial_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RPC error: {e.message}",
        )
    except Exception as e:
        logger.error(f"Error getting signal measurement for device {device.serial_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/{device_id}/ghn-config")
async def get_device_ghn_config(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get G.hn global configuration from device."""
    result = await db.execute(
        select(Device).where(Device.id == device_id)
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    if not device.ip_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device has no IP address configured",
        )

    try:
        client = await create_client_for_device(device)
        ghn_config = await client.get_ghn_global_config()
        ghn_port_config = await client.get_ghn_port_config()
        await client.close()

        return {
            "device_id": str(device.id),
            "serial_number": device.serial_number,
            "global_config": ghn_config,
            "port_config": ghn_port_config,
        }
    except GamRpcError as e:
        logger.error(f"RPC error getting G.hn config for device {device.serial_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RPC error: {e.message}",
        )
    except Exception as e:
        logger.error(f"Error getting G.hn config for device {device.serial_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
