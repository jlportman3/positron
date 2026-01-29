"""
Group model - device groups for organization.
"""
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Group(Base):
    """Device group model for hierarchical organization."""

    __tablename__ = "groups"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Group info
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(512))

    # Parent group for hierarchy
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("groups.id", ondelete="SET NULL"), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(64))
    updated_by: Mapped[Optional[str]] = mapped_column(String(64))

    # Self-referential relationship for hierarchy
    parent: Mapped[Optional["Group"]] = relationship(
        "Group", remote_side=[id], back_populates="children"
    )
    children: Mapped[List["Group"]] = relationship(
        "Group", back_populates="parent", cascade="all, delete-orphan"
    )

    # Devices in this group (back_populates not needed since Device doesn't have relationship)
    devices: Mapped[List["Device"]] = relationship(
        "Device", backref="group", foreign_keys="Device.group_id"
    )

    def __repr__(self) -> str:
        return f"<Group {self.name}>"

    @property
    def device_count(self) -> int:
        """Count of devices in this group."""
        return len(self.devices) if self.devices else 0

    @property
    def full_path(self) -> str:
        """Get full hierarchical path (e.g., 'Parent / Child / Grandchild')."""
        if self.parent:
            return f"{self.parent.full_path} / {self.name}"
        return self.name
