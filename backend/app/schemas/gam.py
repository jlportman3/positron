from pydantic import BaseModel, Field, IPvAnyAddress
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class GAMDeviceDiscoverRequest(BaseModel):
    """Request to discover GAM device via SNMP"""
    ip_address: str = Field(..., description="IP address of the GAM device")
    snmp_community: Optional[str] = Field("public", description="SNMP community string")
    name: Optional[str] = Field(None, description="Optional name for the device")


class GAMDeviceCreate(BaseModel):
    """Create a new GAM device"""
    name: str = Field(..., min_length=1, max_length=255)
    ip_address: str
    model: str = Field(..., description="GAM model (e.g., GAM-12-M, GAM-24-C)")
    mac_address: Optional[str] = None
    firmware_version: Optional[str] = None
    location: Optional[str] = None
    snmp_community: str = "public"
    management_vlan: int = 4093
    serial_number: Optional[str] = None

    # Geographic coordinates
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    zone_id: Optional[UUID] = None


class GAMDeviceUpdate(BaseModel):
    """Update an existing GAM device"""
    name: Optional[str] = None
    location: Optional[str] = None
    snmp_community: Optional[str] = None
    management_vlan: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    zone_id: Optional[UUID] = None


class GAMPortResponse(BaseModel):
    """GAM port information"""
    id: str
    port_number: int
    port_type: str
    status: str
    name: Optional[str] = None
    enabled: bool
    mimo_enabled: bool
    link_speed_down: Optional[int] = None
    link_speed_up: Optional[int] = None
    snr_downstream: Optional[int] = None
    snr_upstream: Optional[int] = None
    subscriber_count: int
    is_available: bool

    class Config:
        from_attributes = True


class GAMDeviceResponse(BaseModel):
    """GAM device information"""
    id: str
    name: str
    ip_address: str
    mac_address: Optional[str] = None
    model: str
    firmware_version: Optional[str] = None
    location: Optional[str] = None
    status: str
    last_seen: Optional[datetime] = None

    # Geographic coordinates
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    zone_id: Optional[str] = None

    # Connection settings
    snmp_community: str
    management_vlan: int

    # Device info
    serial_number: Optional[str] = None
    uptime: Optional[int] = None
    cpu_usage: Optional[int] = None
    memory_usage: Optional[int] = None
    temperature: Optional[int] = None

    # Metadata
    created_at: datetime
    updated_at: datetime

    # Computed properties
    port_count: int
    active_subscribers: int

    # Optional: Include ports if requested
    ports: Optional[List[GAMPortResponse]] = None

    class Config:
        from_attributes = True


class GAMDeviceDiscoverResponse(BaseModel):
    """Response from device discovery"""
    success: bool
    message: str
    device_info: Optional[dict] = None
    device: Optional[GAMDeviceResponse] = None
