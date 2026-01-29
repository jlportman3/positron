"""
Splynx Lookup Task model - tracks pending and completed Splynx inventory lookups.
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SplynxLookupTask(Base):
    """Track Splynx inventory lookup tasks for new endpoints."""

    __tablename__ = "splynx_lookup_tasks"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Endpoint relationship
    endpoint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("endpoints.id", ondelete="CASCADE"), index=True
    )

    # MAC address for lookup (denormalized for convenience)
    mac_address: Mapped[str] = mapped_column(String(32), index=True)

    # Status: pending, found, expired, failed, provisioned
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)

    # Retry tracking
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_attempt_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Splynx result data (when found)
    found_customer_id: Mapped[Optional[int]] = mapped_column(Integer)
    found_customer_name: Mapped[Optional[str]] = mapped_column(String(255))
    found_service_id: Mapped[Optional[int]] = mapped_column(Integer)
    found_tariff_name: Mapped[Optional[str]] = mapped_column(String(255))
    found_inventory_id: Mapped[Optional[int]] = mapped_column(Integer)

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    endpoint: Mapped["Endpoint"] = relationship("Endpoint")

    def __repr__(self) -> str:
        return f"<SplynxLookupTask {self.mac_address} status={self.status} attempts={self.attempts}>"
