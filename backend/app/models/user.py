"""
User model - system users with privilege levels.
"""
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, DateTime, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    """System user model with 16 privilege levels (0-15)."""

    __tablename__ = "users"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Authentication
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))  # BCrypt hashed

    # Status
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_radius: Mapped[bool] = mapped_column(Boolean, default=False)
    is_device: Mapped[bool] = mapped_column(Boolean, default=False)  # Device announcement user

    # Authorization
    privilege_level: Mapped[int] = mapped_column(Integer, default=1)  # 0-15

    # Session settings
    session_timeout: Mapped[int] = mapped_column(Integer, default=30)  # minutes
    timezone: Mapped[Optional[str]] = mapped_column(String(64))

    # Invitation
    invitation_token: Mapped[Optional[str]] = mapped_column(String(64), unique=True, index=True)
    invitation_expires: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Activity tracking
    ip_address: Mapped[Optional[str]] = mapped_column(String(64))
    last_activity: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(64))
    updated_by: Mapped[Optional[str]] = mapped_column(String(64))

    # Relationships
    sessions: Mapped[List["Session"]] = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )
    notification_subscriptions: Mapped[List["NotificationSubscription"]] = relationship(
        "NotificationSubscription", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.username} (level={self.privilege_level})>"

    @property
    def privilege_name(self) -> str:
        """Get human-readable privilege level name."""
        from app.core.security import PRIVILEGE_LEVELS
        return PRIVILEGE_LEVELS.get(self.privilege_level, "Unknown")
