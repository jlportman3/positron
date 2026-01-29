"""
Subscriber schemas.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID


class SubscriberBase(BaseModel):
    """Base subscriber fields."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

    # Bandwidth profile
    bw_profile_id: Optional[int] = None

    # VLAN configuration - Port 1
    port1_vlan_id: Optional[str] = None
    vlan_is_tagged: bool = False
    allowed_tagged_vlan: Optional[str] = None

    # VLAN configuration - Port 2
    port2_vlan_id: Optional[int] = None
    vlan_is_tagged2: bool = False
    allowed_tagged_vlan2: Optional[str] = None

    # Advanced VLAN
    remapped_vlan_id: Optional[int] = None
    double_tags: bool = False
    trunk_mode: bool = False

    # Port configuration
    port_if_index: Optional[str] = None
    nni_if_index: Optional[str] = None
    poe_mode_ctrl: Optional[str] = "auto"  # auto, on, off


class SubscriberCreate(SubscriberBase):
    """Subscriber creation request."""
    device_id: UUID
    endpoint_mac_address: Optional[str] = None  # Can assign to endpoint


class SubscriberUpdate(BaseModel):
    """Subscriber update request (all fields optional)."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    bw_profile_id: Optional[int] = None
    port1_vlan_id: Optional[str] = None
    vlan_is_tagged: Optional[bool] = None
    allowed_tagged_vlan: Optional[str] = None
    port2_vlan_id: Optional[int] = None
    vlan_is_tagged2: Optional[bool] = None
    allowed_tagged_vlan2: Optional[str] = None
    remapped_vlan_id: Optional[int] = None
    double_tags: Optional[bool] = None
    trunk_mode: Optional[bool] = None
    port_if_index: Optional[str] = None
    nni_if_index: Optional[str] = None
    poe_mode_ctrl: Optional[str] = None


class SubscriberResponse(BaseModel):
    """Full subscriber response."""
    id: UUID
    device_id: UUID
    endpoint_id: Optional[UUID] = None

    # GAM identifiers
    json_id: Optional[int] = None
    uid: Optional[int] = None

    # Identification
    name: str
    description: Optional[str] = None

    # Endpoint association
    endpoint_json_id: Optional[int] = None
    endpoint_name: Optional[str] = None
    endpoint_mac_address: Optional[str] = None

    # Bandwidth profile
    bw_profile_id: Optional[int] = None
    bw_profile_name: Optional[str] = None
    bw_profile_uid: Optional[int] = None

    # VLAN configuration
    port1_vlan_id: Optional[str] = None
    vlan_is_tagged: bool = False
    allowed_tagged_vlan: Optional[str] = None
    port2_vlan_id: Optional[int] = None
    vlan_is_tagged2: bool = False
    allowed_tagged_vlan2: Optional[str] = None
    remapped_vlan_id: Optional[int] = None
    double_tags: bool = False
    trunk_mode: bool = False

    # Port configuration
    port_if_index: Optional[str] = None
    nni_if_index: Optional[str] = None
    poe_mode_ctrl: Optional[str] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubscriberList(BaseModel):
    """Paginated subscriber list."""
    items: List[SubscriberResponse]
    total: int
    page: int
    page_size: int
