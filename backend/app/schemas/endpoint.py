"""
Endpoint schemas.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from uuid import UUID


class EndpointBrief(BaseModel):
    """Brief endpoint info for lists."""
    id: UUID
    mac_address: str
    conf_endpoint_name: Optional[str] = None
    conf_endpoint_description: Optional[str] = None
    state: Optional[str] = None
    alive: bool
    model_type: Optional[str] = None
    model_string: Optional[str] = None
    detected_port_if_index: Optional[str] = None
    conf_port_if_index: Optional[str] = None
    rx_phy_rate: Optional[int] = None
    tx_phy_rate: Optional[int] = None
    rx_max_xput: Optional[int] = None
    tx_max_xput: Optional[int] = None
    wire_length_feet: Optional[int] = None
    conf_user_name: Optional[str] = None  # Subscriber name
    conf_bw_profile_name: Optional[str] = None  # Bandwidth profile
    serial_number: Optional[str] = None
    hw_product: Optional[str] = None
    fw_version: Optional[str] = None
    software_revision: Optional[str] = None
    uptime: Optional[str] = None
    port1_link: Optional[bool] = None
    port1_speed: Optional[str] = None
    port2_link: Optional[bool] = None
    port2_speed: Optional[str] = None
    device_id: UUID

    class Config:
        from_attributes = True


class EndpointResponse(BaseModel):
    """Full endpoint response."""
    id: UUID
    device_id: UUID
    mac_address: str

    # Configuration
    conf_endpoint_id: Optional[int] = None
    conf_endpoint_name: Optional[str] = None
    conf_endpoint_description: Optional[str] = None
    conf_port_if_index: Optional[str] = None
    conf_auto_port: bool = False
    detected_port_if_index: Optional[str] = None

    # Subscriber association
    conf_user_id: Optional[int] = None
    conf_user_name: Optional[str] = None
    conf_user_uid: Optional[int] = None
    conf_bw_profile_id: Optional[int] = None
    conf_bw_profile_name: Optional[str] = None

    # Status
    state: Optional[str] = None
    state_code: Optional[str] = None
    custom_state: Optional[str] = None
    alive: bool = False

    # Hardware
    model_type: Optional[str] = None
    model_string: Optional[str] = None
    hw_product: Optional[str] = None
    device_name: Optional[str] = None
    serial_number: Optional[str] = None
    fw_version: Optional[str] = None
    fw_mismatch: bool = False

    # Performance
    mode: Optional[str] = None
    wire_length_meters: Optional[int] = None
    wire_length_feet: Optional[int] = None
    rx_phy_rate: Optional[int] = None
    tx_phy_rate: Optional[int] = None
    rx_alloc_bands: Optional[int] = None
    tx_alloc_bands: Optional[int] = None
    rx_max_xput: Optional[int] = None
    tx_max_xput: Optional[int] = None
    rx_usage: Optional[int] = None
    tx_usage: Optional[int] = None
    uptime: Optional[str] = None

    # Ethernet ports
    port1_link: Optional[bool] = None
    port1_speed: Optional[str] = None
    port2_link: Optional[bool] = None
    port2_speed: Optional[str] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_details_update: Optional[datetime] = None

    class Config:
        from_attributes = True


class EndpointList(BaseModel):
    """Paginated endpoint list."""
    items: List[EndpointBrief]
    total: int
    page: int
    page_size: int
    connected_count: int = 0
    disconnected_count: int = 0
