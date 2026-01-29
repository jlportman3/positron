"""
Port model - physical ports on GAM devices.
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Port(Base):
    """Physical port model for GAM devices."""

    __tablename__ = "ports"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Device relationship
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), index=True
    )

    # Port identification
    key: Mapped[str] = mapped_column(String(32), index=True)  # e.g., "Gi 1/1", "G.hn 1/1"
    position: Mapped[Optional[int]] = mapped_column(Integer)

    # Link status
    link: Mapped[bool] = mapped_column(Boolean, default=False)
    fdx: Mapped[bool] = mapped_column(Boolean, default=False)  # Full duplex
    speed: Mapped[Optional[str]] = mapped_column(String(32))  # e.g., "1000M", "100M"

    # SFP info (for fiber ports)
    fiber: Mapped[bool] = mapped_column(Boolean, default=False)
    sfp_type: Mapped[Optional[str]] = mapped_column(String(64))
    sfp_vendor_name: Mapped[Optional[str]] = mapped_column(String(128))
    sfp_vendor_pn: Mapped[Optional[str]] = mapped_column(String(64))
    sfp_vendor_rev: Mapped[Optional[str]] = mapped_column(String(32))
    sfp_vendor_sn: Mapped[Optional[str]] = mapped_column(String(64))
    present: Mapped[bool] = mapped_column(Boolean, default=False)
    loss_of_signal: Mapped[bool] = mapped_column(Boolean, default=False)
    tx_fault: Mapped[bool] = mapped_column(Boolean, default=False)

    # Configuration
    shutdown: Mapped[bool] = mapped_column(Boolean, default=False)
    mtu: Mapped[int] = mapped_column(Integer, default=1500)
    pfc: Mapped[int] = mapped_column(Integer, default=0)  # Priority Flow Control
    advertise_disabled: Mapped[int] = mapped_column(Integer, default=0)
    media_type: Mapped[Optional[str]] = mapped_column(String(32))
    fc: Mapped[Optional[str]] = mapped_column(String(16))  # Flow control
    rfc5517mode: Mapped[Optional[str]] = mapped_column(String(32))
    excessive_restart: Mapped[bool] = mapped_column(Boolean, default=False)
    frame_length_check: Mapped[bool] = mapped_column(Boolean, default=False)

    # Monitoring
    tca_status: Mapped[Optional[str]] = mapped_column(String(32))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationship
    device: Mapped["Device"] = relationship("Device", back_populates="ports")

    def __repr__(self) -> str:
        status = "UP" if self.link else "DOWN"
        return f"<Port {self.key} ({status})>"
