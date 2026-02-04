"""
Device health history model for tracking health scores over time.
"""
import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Integer, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.device import Device


class DeviceHealthHistory(Base):
    """Stores hourly health score snapshots for historical analysis."""

    __tablename__ = "device_health_history"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Device relationship
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Health metrics snapshot
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, index=True
    )
    health_score: Mapped[int] = mapped_column(Integer, nullable=False)
    sync_success_rate: Mapped[float] = mapped_column(Float, nullable=False)
    avg_response_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    alarm_count: Mapped[int] = mapped_column(Integer, nullable=False)
    uptime_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationship
    device: Mapped["Device"] = relationship("Device", back_populates="health_history")

    def __repr__(self) -> str:
        return f"<DeviceHealthHistory score={self.health_score} at {self.timestamp}>"
