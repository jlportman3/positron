"""
Notification model - alarm notification subscriptions and history.
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class NotificationSubscription(Base):
    """Notification subscription for alarm events."""

    __tablename__ = "notification_subscriptions"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # User this subscription belongs to
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    # Subscription settings
    name: Mapped[str] = mapped_column(String(255))  # e.g., "Critical Alarms"
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Alarm filters
    severities: Mapped[str] = mapped_column(String(64), default="CR,MJ")  # Comma-separated: CR,MJ,MN,NA
    device_ids: Mapped[Optional[str]] = mapped_column(Text)  # Comma-separated UUIDs or null for all
    group_ids: Mapped[Optional[str]] = mapped_column(Text)  # Comma-separated UUIDs or null for all

    # Notification channels
    notify_email: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_webhook: Mapped[bool] = mapped_column(Boolean, default=False)
    webhook_url: Mapped[Optional[str]] = mapped_column(String(512))

    # Rate limiting
    min_interval_minutes: Mapped[int] = mapped_column(default=5)  # Don't send more than once per X minutes for same alarm type
    last_notification_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notification_subscriptions")

    def __repr__(self) -> str:
        return f"<NotificationSubscription {self.name} for user {self.user_id}>"


class NotificationLog(Base):
    """Log of sent notifications."""

    __tablename__ = "notification_logs"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Related subscription
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("notification_subscriptions.id", ondelete="CASCADE"), index=True
    )

    # Related alarm
    alarm_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("alarms.id", ondelete="SET NULL"), index=True
    )

    # Notification details
    channel: Mapped[str] = mapped_column(String(32))  # email, webhook
    recipient: Mapped[str] = mapped_column(String(255))  # email address or webhook URL
    subject: Mapped[Optional[str]] = mapped_column(String(512))
    content: Mapped[Optional[str]] = mapped_column(Text)

    # Status
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending, sent, failed
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    subscription: Mapped["NotificationSubscription"] = relationship("NotificationSubscription")

    def __repr__(self) -> str:
        return f"<NotificationLog {self.channel} {self.status}>"
