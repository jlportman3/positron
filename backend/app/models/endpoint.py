"""
Endpoint model - G.hn CPE devices connected to GAM.
"""
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Endpoint(Base):
    """G.hn Endpoint (CPE) model."""

    __tablename__ = "endpoints"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Device relationship
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), index=True
    )

    # Unique identifier
    mac_address: Mapped[str] = mapped_column(String(32), unique=True, index=True)

    # Configuration from GAM
    conf_endpoint_id: Mapped[Optional[int]] = mapped_column(Integer)
    conf_endpoint_name: Mapped[Optional[str]] = mapped_column(String(255))
    conf_endpoint_description: Mapped[Optional[str]] = mapped_column(String(512))
    conf_port_if_index: Mapped[Optional[str]] = mapped_column(String(32))
    conf_auto_port: Mapped[bool] = mapped_column(Boolean, default=False)
    detected_port_if_index: Mapped[Optional[str]] = mapped_column(String(32))

    # User/subscriber association
    conf_user_id: Mapped[Optional[int]] = mapped_column(Integer)
    conf_user_name: Mapped[Optional[str]] = mapped_column(String(255))
    conf_user_uid: Mapped[Optional[int]] = mapped_column(Integer)

    # Bandwidth profile
    conf_bw_profile_id: Mapped[Optional[int]] = mapped_column(Integer)
    conf_bw_profile_name: Mapped[Optional[str]] = mapped_column(String(255))
    conf_bw_profile_uid: Mapped[Optional[int]] = mapped_column(Integer)

    # Status
    state: Mapped[Optional[str]] = mapped_column(String(32))  # connected, disconnected, etc.
    state_code: Mapped[Optional[str]] = mapped_column(String(32))
    custom_state: Mapped[Optional[str]] = mapped_column(String(64))
    alive: Mapped[bool] = mapped_column(Boolean, default=False)

    # Hardware info
    model_type: Mapped[Optional[str]] = mapped_column(String(64))
    model_string: Mapped[Optional[str]] = mapped_column(String(128))
    hw_product: Mapped[Optional[str]] = mapped_column(String(128))
    device_name: Mapped[Optional[str]] = mapped_column(String(255))
    serial_number: Mapped[Optional[str]] = mapped_column(String(64))
    fw_version: Mapped[Optional[str]] = mapped_column(String(64))
    fw_mismatch: Mapped[bool] = mapped_column(Boolean, default=False)

    # Performance metrics
    mode: Mapped[Optional[str]] = mapped_column(String(16))  # MIMO/SISO
    wire_length_meters: Mapped[Optional[int]] = mapped_column(Integer)
    wire_length_feet: Mapped[Optional[int]] = mapped_column(Integer)
    rx_phy_rate: Mapped[Optional[int]] = mapped_column(Integer)  # Mbps
    tx_phy_rate: Mapped[Optional[int]] = mapped_column(Integer)  # Mbps
    rx_alloc_bands: Mapped[Optional[int]] = mapped_column(Integer)
    tx_alloc_bands: Mapped[Optional[int]] = mapped_column(Integer)
    rx_max_xput: Mapped[Optional[int]] = mapped_column(Integer)
    tx_max_xput: Mapped[Optional[int]] = mapped_column(Integer)
    rx_usage: Mapped[Optional[int]] = mapped_column(Integer)  # percentage
    tx_usage: Mapped[Optional[int]] = mapped_column(Integer)  # percentage
    xput_indicator: Mapped[Optional[int]] = mapped_column(Integer)
    uptime: Mapped[Optional[str]] = mapped_column(String(64))
    uptime_seconds: Mapped[Optional[int]] = mapped_column(Integer)

    # Ethernet ports
    auto_port: Mapped[bool] = mapped_column(Boolean, default=False)
    eth_port1_shutdown: Mapped[bool] = mapped_column(Boolean, default=False)
    eth_port2_shutdown: Mapped[bool] = mapped_column(Boolean, default=False)

    # Port 1 status
    port1_valid: Mapped[Optional[bool]] = mapped_column(Boolean)
    port1_link: Mapped[Optional[bool]] = mapped_column(Boolean)
    port1_fdx: Mapped[Optional[bool]] = mapped_column(Boolean)
    port1_speed: Mapped[Optional[str]] = mapped_column(String(16))
    port1_display: Mapped[Optional[str]] = mapped_column(String(64))

    # Port 2 status
    port2_valid: Mapped[Optional[bool]] = mapped_column(Boolean)
    port2_link: Mapped[Optional[bool]] = mapped_column(Boolean)
    port2_fdx: Mapped[Optional[bool]] = mapped_column(Boolean)
    port2_speed: Mapped[Optional[str]] = mapped_column(String(16))
    port2_display: Mapped[Optional[str]] = mapped_column(String(64))

    # Quarantine
    quarantined: Mapped[bool] = mapped_column(Boolean, default=False)
    quarantine_reason: Mapped[Optional[str]] = mapped_column(String(512))

    # Monitoring
    tca_status: Mapped[Optional[str]] = mapped_column(String(32))
    last_details_update: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    device: Mapped["Device"] = relationship("Device", back_populates="endpoints")
    subscribers: Mapped[List["Subscriber"]] = relationship(
        "Subscriber", back_populates="endpoint", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Endpoint {self.mac_address} ({self.conf_endpoint_name})>"
