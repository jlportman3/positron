"""
Sync attempt tracking model.
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SyncAttempt(Base):
    """Tracks individual sync operation attempts for health scoring."""

    __tablename__ = "sync_attempts"

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

    # Sync operation details
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, index=True
    )
    operation: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # endpoints/subscribers/bandwidths/ports
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationship
    device: Mapped["Device"] = relationship("Device", back_populates="sync_attempts")

    def __repr__(self) -> str:
        return f"<SyncAttempt {self.operation} {'OK' if self.success else 'FAIL'} {self.duration_ms}ms>"
