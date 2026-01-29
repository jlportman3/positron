"""
Device model - represents a GAM device.
"""
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Device(Base):
    """GAM Device model."""

    __tablename__ = "devices"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Core identification
    serial_number: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    mac_address: Mapped[Optional[str]] = mapped_column(String(32))
    name: Mapped[Optional[str]] = mapped_column(String(255))
    vendor: Mapped[Optional[str]] = mapped_column(String(128))
    product_class: Mapped[Optional[str]] = mapped_column(String(128))
    hardware_version: Mapped[Optional[str]] = mapped_column(String(64))
    compatible: Mapped[Optional[str]] = mapped_column(String(128))
    uni_ports: Mapped[Optional[str]] = mapped_column(String(16))
    clei_code: Mapped[Optional[str]] = mapped_column(String(64))

    # Network
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    fqdn: Mapped[Optional[str]] = mapped_column(String(255))
    proto: Mapped[str] = mapped_column(String(8), default="https")
    port: Mapped[str] = mapped_column(String(8), default="443")

    # Software
    software_version: Mapped[Optional[str]] = mapped_column(String(64))
    software_revision: Mapped[Optional[str]] = mapped_column(String(64))
    software_build_date: Mapped[Optional[str]] = mapped_column(String(32))
    firmware: Mapped[Optional[str]] = mapped_column(String(128))
    firmware_encryption_key_id: Mapped[Optional[str]] = mapped_column(String(64))
    software_upgrade_status: Mapped[Optional[str]] = mapped_column(String(64))

    # Alternate firmware (swap partition)
    swap_software_version: Mapped[Optional[str]] = mapped_column(String(64))
    swap_software_revision: Mapped[Optional[str]] = mapped_column(String(64))
    swap_software_build_date: Mapped[Optional[str]] = mapped_column(String(32))

    # Announcement settings
    announcement_period: Mapped[Optional[str]] = mapped_column(String(16))
    announcement_url: Mapped[Optional[str]] = mapped_column(String(512))

    # Credentials (encrypted tokens from announcement - NOT for direct RPC use)
    user_name: Mapped[Optional[str]] = mapped_column(String(64))
    password: Mapped[Optional[str]] = mapped_column(String(128))

    # Plaintext RPC credentials (for JSON-RPC communication with device)
    rpc_username: Mapped[Optional[str]] = mapped_column(String(64))
    rpc_password: Mapped[Optional[str]] = mapped_column(String(128))

    # Multi-level credentials (0-15)
    user_name_level0: Mapped[Optional[str]] = mapped_column(String(64))
    password_level0: Mapped[Optional[str]] = mapped_column(String(128))
    user_name_level1: Mapped[Optional[str]] = mapped_column(String(64))
    password_level1: Mapped[Optional[str]] = mapped_column(String(128))
    user_name_level2: Mapped[Optional[str]] = mapped_column(String(64))
    password_level2: Mapped[Optional[str]] = mapped_column(String(128))
    user_name_level3: Mapped[Optional[str]] = mapped_column(String(64))
    password_level3: Mapped[Optional[str]] = mapped_column(String(128))
    user_name_level4: Mapped[Optional[str]] = mapped_column(String(64))
    password_level4: Mapped[Optional[str]] = mapped_column(String(128))
    user_name_level5: Mapped[Optional[str]] = mapped_column(String(64))
    password_level5: Mapped[Optional[str]] = mapped_column(String(128))
    user_name_level6: Mapped[Optional[str]] = mapped_column(String(64))
    password_level6: Mapped[Optional[str]] = mapped_column(String(128))
    user_name_level7: Mapped[Optional[str]] = mapped_column(String(64))
    password_level7: Mapped[Optional[str]] = mapped_column(String(128))
    user_name_level8: Mapped[Optional[str]] = mapped_column(String(64))
    password_level8: Mapped[Optional[str]] = mapped_column(String(128))
    user_name_level9: Mapped[Optional[str]] = mapped_column(String(64))
    password_level9: Mapped[Optional[str]] = mapped_column(String(128))
    user_name_level10: Mapped[Optional[str]] = mapped_column(String(64))
    password_level10: Mapped[Optional[str]] = mapped_column(String(128))
    user_name_level11: Mapped[Optional[str]] = mapped_column(String(64))
    password_level11: Mapped[Optional[str]] = mapped_column(String(128))
    user_name_level12: Mapped[Optional[str]] = mapped_column(String(64))
    password_level12: Mapped[Optional[str]] = mapped_column(String(128))
    user_name_level13: Mapped[Optional[str]] = mapped_column(String(64))
    password_level13: Mapped[Optional[str]] = mapped_column(String(128))
    user_name_level14: Mapped[Optional[str]] = mapped_column(String(64))
    password_level14: Mapped[Optional[str]] = mapped_column(String(128))
    user_name_level15: Mapped[Optional[str]] = mapped_column(String(64))
    password_level15: Mapped[Optional[str]] = mapped_column(String(128))

    # SSH Tunnel
    remote_port_tunnel: Mapped[int] = mapped_column(Integer, default=0)
    remote_port_tunnel_index: Mapped[int] = mapped_column(Integer, default=0)

    # Status
    is_virtual: Mapped[bool] = mapped_column(Boolean, default=False)  # SGAM
    is_online: Mapped[bool] = mapped_column(Boolean, default=False)
    read_only: Mapped[bool] = mapped_column(Boolean, default=False)  # Prevent write operations
    uptime: Mapped[Optional[int]] = mapped_column(Integer)  # seconds

    # Location/Contact
    location: Mapped[Optional[str]] = mapped_column(String(255))
    contact: Mapped[Optional[str]] = mapped_column(String(255))

    # Group
    group_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("groups.id"), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_announcement: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Polling timestamps
    last_port_pulled: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_endpoint_brief_pulled: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_endpoint_detail_pulled: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_subscriber_pulled: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_bandwidth_pulled: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_uptime_pulled: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_config_backup: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Config backup
    config_backup: Mapped[Optional[str]] = mapped_column(Text)

    # Optimistic locking
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Relationships
    endpoints: Mapped[List["Endpoint"]] = relationship(
        "Endpoint", back_populates="device", cascade="all, delete-orphan"
    )
    subscribers: Mapped[List["Subscriber"]] = relationship(
        "Subscriber", back_populates="device", cascade="all, delete-orphan"
    )
    bandwidths: Mapped[List["Bandwidth"]] = relationship(
        "Bandwidth", back_populates="device", cascade="all, delete-orphan"
    )
    ports: Mapped[List["Port"]] = relationship(
        "Port", back_populates="device", cascade="all, delete-orphan"
    )
    alarms: Mapped[List["Alarm"]] = relationship(
        "Alarm", back_populates="device", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Device {self.serial_number} ({self.name})>"
