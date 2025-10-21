"""GAM device API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from ...database import get_db
from ...services.gam_manager import GAMManager
from ...models.gam import DeviceStatus

router = APIRouter()


# Pydantic schemas
class GAMDeviceCreate(BaseModel):
    name: str
    ip_address: str
    model: str
    snmp_community: Optional[str] = None
    ssh_credentials: Optional[dict] = None
    location: Optional[str] = None
    management_vlan: Optional[int] = None


class GAMDeviceUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    status: Optional[DeviceStatus] = None
    snmp_community: Optional[str] = None
    ssh_credentials: Optional[dict] = None


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
