"""
Alarm schemas.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from uuid import UUID


class AlarmResponse(BaseModel):
    """Alarm response."""
    id: UUID
    device_id: UUID

    # Identifiers
    gam_id: Optional[str] = None
    if_index: Optional[str] = None
    if_descr: Optional[str] = None

    # Alarm details
    cond_type: str
    severity: str  # CR, MJ, MN, NA
    serv_aff: Optional[str] = None
    details: Optional[str] = None

    # Status
    is_active: bool
    is_critical: bool
    is_service_affecting: bool

    # Timestamps
    occur_time: Optional[str] = None
    occurred_at: datetime
    closing_date: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None

    # Flags
    is_manual: bool = False

    # Device info (for lists)
    device_serial: Optional[str] = None
    device_name: Optional[str] = None

    class Config:
        from_attributes = True


class AlarmList(BaseModel):
    """Paginated alarm list."""
    items: List[AlarmResponse]
    total: int
    page: int
    page_size: int


class AlarmCounts(BaseModel):
    """Alarm count summary by severity."""
    critical: int = 0  # CR
    major: int = 0     # MJ
    minor: int = 0     # MN
    normal: int = 0    # NA
    total: int = 0
