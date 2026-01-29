"""
Timezone model - timezone configuration for GAM devices.
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Timezone(Base):
    """Timezone configuration model."""

    __tablename__ = "timezones"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    offset: Mapped[str] = mapped_column(String(16))  # e.g., "UTC-06:00"
    dst_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    dst_start: Mapped[Optional[str]] = mapped_column(String(128))  # e.g., "Second Sunday in March"
    dst_end: Mapped[Optional[str]] = mapped_column(String(128))  # e.g., "First Sunday in November"

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<Timezone {self.name} ({self.offset})>"
