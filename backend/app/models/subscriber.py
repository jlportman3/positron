"""
Subscriber model - service subscribers on GAM devices.
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Subscriber(Base):
    """Subscriber/user service model."""

    __tablename__ = "subscribers"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Device relationship
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), index=True
    )

    # Endpoint relationship (optional - subscriber can exist without endpoint)
    endpoint_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("endpoints.id", ondelete="SET NULL"), nullable=True
    )

    # GAM-side identifiers
    json_id: Mapped[Optional[int]] = mapped_column(Integer)  # ID from JSON-RPC
    uid: Mapped[Optional[int]] = mapped_column(Integer)

    # Identification
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[Optional[str]] = mapped_column(String(512))

    # Endpoint association (from GAM)
    endpoint_json_id: Mapped[Optional[int]] = mapped_column(Integer)
    endpoint_name: Mapped[Optional[str]] = mapped_column(String(255))
    endpoint_mac_address: Mapped[Optional[str]] = mapped_column(String(32))

    # Bandwidth profile
    bw_profile_id: Mapped[Optional[int]] = mapped_column(Integer)
    bw_profile_name: Mapped[Optional[str]] = mapped_column(String(255))
    bw_profile_uid: Mapped[Optional[int]] = mapped_column(Integer)

    # VLAN Configuration - Port 1
    port1_vlan_id: Mapped[Optional[str]] = mapped_column(String(16))
    vlan_is_tagged: Mapped[bool] = mapped_column(Boolean, default=False)
    allowed_tagged_vlan: Mapped[Optional[str]] = mapped_column(String(255))

    # VLAN Configuration - Port 2
    port2_vlan_id: Mapped[Optional[int]] = mapped_column(Integer)
    vlan_is_tagged2: Mapped[bool] = mapped_column(Boolean, default=False)
    allowed_tagged_vlan2: Mapped[Optional[str]] = mapped_column(String(255))

    # Advanced VLAN
    remapped_vlan_id: Mapped[Optional[int]] = mapped_column(Integer)
    double_tags: Mapped[bool] = mapped_column(Boolean, default=False)
    trunk_mode: Mapped[bool] = mapped_column(Boolean, default=False)

    # Port configuration
    port_if_index: Mapped[Optional[str]] = mapped_column(String(32))
    nni_if_index: Mapped[Optional[str]] = mapped_column(String(32))
    poe_mode_ctrl: Mapped[Optional[str]] = mapped_column(String(32))  # auto, on, off

    # Status
    alive: Mapped[bool] = mapped_column(Boolean, default=False)

    # Splynx integration
    splynx_customer_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    splynx_service_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    device: Mapped["Device"] = relationship("Device", back_populates="subscribers")
    endpoint: Mapped[Optional["Endpoint"]] = relationship(
        "Endpoint", back_populates="subscribers"
    )

    def __repr__(self) -> str:
        return f"<Subscriber {self.name} ({self.endpoint_mac_address})>"
