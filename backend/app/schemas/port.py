"""
Port schemas.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from uuid import UUID


class PortResponse(BaseModel):
    """Port response."""
    id: UUID
    device_id: UUID
    key: str
    position: Optional[int] = None
    link: bool = False
    fdx: bool = False
    speed: Optional[str] = None
    fiber: bool = False
    sfp_type: Optional[str] = None
    sfp_vendor_name: Optional[str] = None
    sfp_vendor_pn: Optional[str] = None
    sfp_vendor_rev: Optional[str] = None
    sfp_vendor_sn: Optional[str] = None
    present: bool = False
    loss_of_signal: bool = False
    tx_fault: bool = False
    shutdown: bool = False
    mtu: int = 1500
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PortBrief(BaseModel):
    """Brief port info for lists."""
    id: UUID
    key: str
    link: bool
    speed: Optional[str] = None
    fiber: bool = False
    sfp_type: Optional[str] = None

    class Config:
        from_attributes = True


class PortList(BaseModel):
    """Paginated port list."""
    items: List[PortResponse]
    total: int
    device_id: Optional[UUID] = None


class PortUpdate(BaseModel):
    """Port update schema - configurable settings only."""
    shutdown: Optional[bool] = None
    mtu: Optional[int] = None


class PortWithDevice(PortResponse):
    """Port with device name for list views."""
    device_name: Optional[str] = None
    device_serial: Optional[str] = None
