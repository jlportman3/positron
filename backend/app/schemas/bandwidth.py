"""
Bandwidth profile schemas.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID


class BandwidthBase(BaseModel):
    """Base bandwidth profile fields."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    ds_bw: int = Field(0, ge=0)  # Downstream in kbps
    us_bw: int = Field(0, ge=0)  # Upstream in kbps


class BandwidthCreate(BandwidthBase):
    """Bandwidth profile creation request."""
    device_id: UUID


class BandwidthUpdate(BaseModel):
    """Bandwidth profile update request."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    ds_bw: Optional[int] = Field(None, ge=0)
    us_bw: Optional[int] = Field(None, ge=0)


class BandwidthResponse(BaseModel):
    """Bandwidth profile response."""
    id: UUID
    device_id: UUID
    uid: Optional[int] = None
    name: str
    description: Optional[str] = None
    ds_bw: int
    us_bw: int
    ds_mbps: float
    us_mbps: float
    sync: bool = False
    sync_error: Optional[str] = None
    deleted: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BandwidthList(BaseModel):
    """Paginated bandwidth profile list."""
    items: List[BandwidthResponse]
    total: int
    page: int
    page_size: int
