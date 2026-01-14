"""GAM device API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
import logging

from ...database import get_db
from ...services.gam_manager import GAMManager
from ...models.gam import DeviceStatus
from ...utils.snmp_client import SNMPClient

router = APIRouter()
logger = logging.getLogger(__name__)


# Pydantic schemas
class GAMDeviceCreate(BaseModel):
    name: str
    ip_address: str
    model: str
    snmp_community: Optional[str] = None
    ssh_credentials: Optional[dict] = None  # Legacy JSONB field
    ssh_username: Optional[str] = None
    ssh_password: Optional[str] = None
    ssh_port: Optional[int] = 22
    location: Optional[str] = None
    management_vlan: Optional[int] = None


class GAMDeviceUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    status: Optional[DeviceStatus] = None
    snmp_community: Optional[str] = None
    ssh_credentials: Optional[dict] = None  # Legacy JSONB field
    ssh_username: Optional[str] = None
    ssh_password: Optional[str] = None
    ssh_port: Optional[int] = None


class GAMDeviceResponse(BaseModel):
    id: UUID
    name: str
    ip_address: str
    model: str
    status: DeviceStatus
    location: Optional[str]
    firmware_version: Optional[str]
    uptime: Optional[int]
    cpu_usage: Optional[int]
    memory_usage: Optional[int]
    ssh_username: Optional[str]  # Include SSH username in response (not password for security)
    ssh_port: Optional[int]

    class Config:
        from_attributes = True


class PortResponse(BaseModel):
    id: UUID
    port_number: int
    port_type: str
    status: str
    enabled: bool
    name: Optional[str]

    class Config:
        from_attributes = True


@router.post("/devices", response_model=GAMDeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    device: GAMDeviceCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create new GAM device"""
    manager = GAMManager(db)
    new_device = await manager.create_device(
        name=device.name,
        ip_address=device.ip_address,
        model=device.model,
        snmp_community=device.snmp_community,
        ssh_credentials=device.ssh_credentials,
        location=device.location,
        management_vlan=device.management_vlan
    )
    return new_device


@router.get("/devices", response_model=List[GAMDeviceResponse])
async def list_devices(
    status: Optional[DeviceStatus] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List all GAM devices"""
    manager = GAMManager(db)
    devices = await manager.list_devices(status=status, limit=limit, offset=offset)
    return devices


@router.get("/devices/{device_id}", response_model=GAMDeviceResponse)
async def get_device(
    device_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get specific GAM device"""
    manager = GAMManager(db)
    device = await manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.put("/devices/{device_id}", response_model=GAMDeviceResponse)
async def update_device(
    device_id: UUID,
    updates: GAMDeviceUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update GAM device"""
    manager = GAMManager(db)
    device = await manager.update_device(
        device_id,
        **updates.model_dump(exclude_unset=True)
    )
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete GAM device"""
    manager = GAMManager(db)
    success = await manager.delete_device(device_id)
    if not success:
        raise HTTPException(status_code=404, detail="Device not found")


@router.get("/devices/{device_id}/ports", response_model=List[PortResponse])
async def get_device_ports(
    device_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get all ports for a device"""
    manager = GAMManager(db)
    ports = await manager.get_device_ports(device_id)
    return ports


@router.post("/devices/{device_id}/test")
async def test_device_connectivity(
    device_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Test device connectivity"""
    manager = GAMManager(db)
    result = await manager.test_device_connectivity(device_id)
    return result


@router.post("/devices/{device_id}/status")
async def update_device_status(
    device_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Update device status from SNMP"""
    manager = GAMManager(db)
    result = await manager.update_device_status(device_id)
    return result


@router.post("/devices/{device_id}/sync-ports")
async def sync_device_ports(
    device_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Sync port status and information from GAM device via SNMP"""
    manager = GAMManager(db)

    # Get device
    device = await manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Create SNMP client
    snmp_client = SNMPClient(
        ip_address=device.ip_address,
        community=device.snmp_community
    )

    # Get port status from device
    logger.info(f"Syncing port status for device {device.name} ({device.ip_address})")
    port_info = await snmp_client.get_gam_ports_info()

    if not port_info:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to query port information from device {device.ip_address}"
        )

    # Update ports in database
    updated_ports = await manager.update_ports_from_snmp(device_id, port_info)

    return {
        "success": True,
        "message": f"Successfully synced {len(updated_ports)} ports",
        "ports": updated_ports,
        "device_id": str(device_id)
    }


class GAMDiscoverRequest(BaseModel):
    ip_address: str
    snmp_community: Optional[str] = "public"
    name: Optional[str] = None
    ssh_username: Optional[str] = None
    ssh_password: Optional[str] = None
    ssh_port: Optional[int] = 22


@router.post("/devices/discover")
async def discover_gam_device(
    request: GAMDiscoverRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Discover GAM device by IP address via SNMP.
    This will query the device, extract its information, and optionally add it to the database.
    """
    logger.info(f"Attempting to discover GAM device at {request.ip_address}")

    # Create SNMP client
    snmp_client = SNMPClient(
        ip_address=request.ip_address,
        community=request.snmp_community
    )

    # Discover device information
    device_info = await snmp_client.discover_gam_device()

    if not device_info:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to discover GAM device at {request.ip_address}. Check IP address and SNMP community string."
        )

    # Check if device already exists
    manager = GAMManager(db)
    existing_device = await manager.get_device_by_ip(request.ip_address)

    if existing_device:
        return {
            "success": True,
            "message": "Device already exists in database",
            "device_info": device_info,
            "device_id": str(existing_device.id),
            "already_exists": True
        }

    # Create device in database
    device_name = request.name or device_info.get('system_name') or f"GAM-{request.ip_address}"

    new_device = await manager.create_device(
        name=device_name,
        ip_address=request.ip_address,
        model=device_info.get('model', 'GAM-Unknown'),
        snmp_community=request.snmp_community,
        ssh_username=request.ssh_username,
        ssh_password=request.ssh_password,
        ssh_port=request.ssh_port,
        mac_address=device_info.get('mac_address'),
        firmware_version=device_info.get('firmware_version'),
        serial_number=device_info.get('serial_number'),
    )

    logger.info(f"Successfully discovered and added GAM device {device_name} at {request.ip_address}")

    return {
        "success": True,
        "message": f"Successfully discovered and added GAM device {device_name}",
        "device_info": device_info,
        "device_id": str(new_device.id),
        "device": new_device
    }


@router.get("/devices/{device_id}/discovered-cpe")
async def get_discovered_cpe(
    device_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Discover all CPE devices connected to this GAM via SSH CLI.
    Executes 'show ghn endpoint' and 'show ghn subscriber' commands.
    Returns Positron G.hn endpoints found on the device.
    """
    manager = GAMManager(db)

    # Get device
    device = await manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Check if SSH credentials are configured
    if not device.ssh_username or not device.ssh_password:
        raise HTTPException(
            status_code=400,
            detail="SSH credentials not configured for this device. Please update device settings with SSH username and password."
        )

    # Create SSH client
    from ...utils.ssh_client import SSHClient
    ssh_client = SSHClient(
        ip_address=device.ip_address,
        username=device.ssh_username,
        password=device.ssh_password,
        timeout=30
    )

    logger.info(f"Discovering CPE devices on {device.name} ({device.ip_address}) via SSH CLI")

    # Get endpoints from device via CLI
    endpoints = await ssh_client.get_ghn_endpoints()
    if endpoints is None:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to query G.hn endpoints from device via SSH. Check SSH credentials and connectivity."
        )

    # Get subscribers from device via CLI
    device_subscribers = await ssh_client.get_ghn_subscribers()
    if device_subscribers is None:
        device_subscribers = []

    # Get configured subscribers from database
    from sqlalchemy import select
    from ...models.subscriber import Subscriber

    result = await db.execute(
        select(Subscriber).where(Subscriber.gam_device_id == device_id)
    )
    db_subscribers = list(result.scalars().all())

    # Create a mapping of endpoint MAC to database subscriber
    configured_macs = {sub.endpoint_mac.lower(): sub for sub in db_subscribers if sub.endpoint_mac}

    # Separate configured vs unconfigured
    unconfigured_cpe = []
    configured_cpe = []

    for endpoint in endpoints:
        mac = endpoint['mac_address'].lower()

        endpoint_data = {
            'mac_address': endpoint['mac_address'],
            'port': endpoint['port'],
            'gam_device_id': str(device_id),
            'gam_device_name': device.name,
            'configured': endpoint.get('configured', 'unknown'),
            'is_up': endpoint.get('is_up', 'unknown'),
        }

        # Check if configured in database
        if mac in configured_macs:
            db_sub = configured_macs[mac]
            endpoint_data['subscriber_id'] = str(db_sub.id)
            endpoint_data['subscriber_name'] = db_sub.name
            endpoint_data['vlan_id'] = db_sub.vlan_id
            endpoint_data['status'] = db_sub.status
            configured_cpe.append(endpoint_data)
        else:
            # Check if configured on device but not in database
            # Find device subscriber by matching MAC address from endpoint
            device_sub = None
            for s in device_subscribers:
                # We need to correlate device subscribers with discovered endpoints
                # For now, mark as unconfigured in management system
                pass

            endpoint_data['configured_on_device'] = endpoint.get('configured', 'no') == 'yes'
            endpoint_data['configured_in_db'] = False

            unconfigured_cpe.append(endpoint_data)

    return {
        'success': True,
        'device_id': str(device_id),
        'device_name': device.name,
        'discovery_method': 'SSH CLI',
        'total_endpoints': len(endpoints),
        'unconfigured_count': len(unconfigured_cpe),
        'configured_count': len(configured_cpe),
        'unconfigured_cpe': unconfigured_cpe,
        'configured_cpe': configured_cpe,
        'device_subscribers': device_subscribers,
    }
