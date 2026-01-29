"""
Alarm model - device alarms and events.
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Alarm(Base):
    """Device alarm model."""

    __tablename__ = "alarms"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Device relationship
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), index=True
    )

    # GAM-side identifiers
    gam_id: Mapped[Optional[str]] = mapped_column(String(64))
    if_index: Mapped[Optional[str]] = mapped_column(String(32))
    if_descr: Mapped[Optional[str]] = mapped_column(String(255))

    # Alarm details
    cond_type: Mapped[str] = mapped_column(String(128), index=True)  # Condition type
    severity: Mapped[str] = mapped_column(String(8), index=True)  # CR, MJ, MN, NA
    serv_aff: Mapped[Optional[str]] = mapped_column(String(8))  # Service affecting (Y/N)
    details: Mapped[Optional[str]] = mapped_column(String(512))

    # Timestamps
    occur_time: Mapped[Optional[str]] = mapped_column(String(64))  # From device
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    closing_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    acknowledged_by: Mapped[Optional[str]] = mapped_column(String(64))

    # Manual flag
    is_manual: Mapped[bool] = mapped_column(Boolean, default=False)

    # Software fault info
    sw_fault_file_name: Mapped[Optional[str]] = mapped_column(String(255))
    sw_fault_line: Mapped[Optional[str]] = mapped_column(String(32))
    sw_fault_module_id: Mapped[Optional[str]] = mapped_column(String(64))

    # Hardware fault info
    hw_fault_id: Mapped[Optional[str]] = mapped_column(String(64))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationship
    device: Mapped["Device"] = relationship("Device", back_populates="alarms")

    def __repr__(self) -> str:
        return f"<Alarm {self.severity} {self.cond_type}>"

    @property
    def is_active(self) -> bool:
        """Check if alarm is still active (not closed)."""
        return self.closing_date is None

    @property
    def is_critical(self) -> bool:
        """Check if alarm is critical severity."""
        return self.severity == "CR"

    @property
    def is_service_affecting(self) -> bool:
        """Check if alarm is service affecting."""
        return self.serv_aff == "Y"
