"""
Setting schemas.
"""
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel


class SettingResponse(BaseModel):
    """Single setting response."""
    key: str
    type: str
    value: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True


class SettingUpdate(BaseModel):
    """Update a single setting."""
    value: str


class SettingsBulkUpdate(BaseModel):
    """Update multiple settings at once."""
    settings: Dict[str, str]


class SettingsList(BaseModel):
    """List of settings grouped by type."""
    items: List[SettingResponse]
    total: int


class SettingsByType(BaseModel):
    """Settings organized by type."""
    device: List[SettingResponse] = []
    endpoint: List[SettingResponse] = []
    polling: List[SettingResponse] = []
    general: List[SettingResponse] = []
    timezone: List[SettingResponse] = []
    ntp: List[SettingResponse] = []
    email: List[SettingResponse] = []
    purge: List[SettingResponse] = []
    firmware: List[SettingResponse] = []
