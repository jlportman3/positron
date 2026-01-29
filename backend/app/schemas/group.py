"""
Group schemas.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID


class GroupBase(BaseModel):
    """Base group fields."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class GroupCreate(GroupBase):
    """Group creation request."""
    parent_id: Optional[UUID] = None


class GroupUpdate(BaseModel):
    """Group update request."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    parent_id: Optional[UUID] = None


class GroupResponse(BaseModel):
    """Group response."""
    id: UUID
    name: str
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    parent_name: Optional[str] = None
    device_count: int = 0
    child_count: int = 0
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True


class GroupTree(BaseModel):
    """Group tree node with children for hierarchical display."""
    id: UUID
    name: str
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    device_count: int = 0
    children: List["GroupTree"] = []

    class Config:
        from_attributes = True


# Enable recursive model
GroupTree.model_rebuild()


class GroupList(BaseModel):
    """Paginated group list."""
    items: List[GroupResponse]
    total: int
    page: int
    page_size: int


class GroupDeviceAssignment(BaseModel):
    """Assign devices to a group."""
    device_ids: List[UUID]


class GroupDeviceResponse(BaseModel):
    """Device info for group membership."""
    id: UUID
    serial_number: str
    name: Optional[str] = None
    is_online: bool = False
