"""
Audit log schemas.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from uuid import UUID


class AuditLogResponse(BaseModel):
    """Audit log entry response."""
    id: UUID
    user_id: Optional[UUID] = None
    username: str
    ip_address: Optional[str] = None
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    entity_name: Optional[str] = None
    description: Optional[str] = None
    old_values: Optional[str] = None
    new_values: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogList(BaseModel):
    """Paginated audit log list."""
    items: List[AuditLogResponse]
    total: int
    page: int
    page_size: int


class AuditLogStats(BaseModel):
    """Audit log statistics."""
    total_entries: int
    entries_today: int
    entries_this_week: int
    top_users: List[dict]
    top_actions: List[dict]
