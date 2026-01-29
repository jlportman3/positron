"""
Bandwidth model - bandwidth profiles for subscribers.
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Bandwidth(Base):
    """Bandwidth profile model."""

    __tablename__ = "bandwidths"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Device relationship
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), index=True
    )

    # GAM-side identifiers
    uid: Mapped[Optional[int]] = mapped_column(Integer)

    # Profile info
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[Optional[str]] = mapped_column(String(512))

    # Bandwidth rates (in kbps)
    ds_bw: Mapped[int] = mapped_column(Integer, default=0)  # Downstream
    us_bw: Mapped[int] = mapped_column(Integer, default=0)  # Upstream

    # Sync status
    sync: Mapped[bool] = mapped_column(Boolean, default=False)
    sync_values: Mapped[Optional[str]] = mapped_column(String(255))
    sync_error: Mapped[Optional[str]] = mapped_column(String(512))

    # Soft delete
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationship
    device: Mapped["Device"] = relationship("Device", back_populates="bandwidths")

    def __repr__(self) -> str:
        return f"<Bandwidth {self.name} ({self.ds_bw}/{self.us_bw} Mbps)>"

    @property
    def ds_mbps(self) -> float:
        """Downstream bandwidth in Mbps (device stores in Mbps)."""
        return float(self.ds_bw) if self.ds_bw else 0

    @property
    def us_mbps(self) -> float:
        """Upstream bandwidth in Mbps (device stores in Mbps)."""
        return float(self.us_bw) if self.us_bw else 0
