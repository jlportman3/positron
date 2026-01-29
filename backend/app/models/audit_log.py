"""
AuditLog model - audit trail for all write operations.
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditLog(Base):
    """Audit log model for tracking all changes."""

    __tablename__ = "audit_logs"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Who
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), index=True)
    username: Mapped[str] = mapped_column(String(64), index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64))

    # What
    action: Mapped[str] = mapped_column(String(32), index=True)  # CREATE, UPDATE, DELETE
    entity_type: Mapped[str] = mapped_column(String(64), index=True)  # Device, Subscriber, etc.
    entity_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    entity_name: Mapped[Optional[str]] = mapped_column(String(255))

    # Details
    description: Mapped[Optional[str]] = mapped_column(String(512))
    old_values: Mapped[Optional[str]] = mapped_column(Text)  # JSON of old values
    new_values: Mapped[Optional[str]] = mapped_column(Text)  # JSON of new values

    # When
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} {self.entity_type} by {self.username}>"
