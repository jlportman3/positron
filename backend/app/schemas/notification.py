"""
Notification schemas for API requests and responses.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class NotificationSubscriptionBase(BaseModel):
    """Base notification subscription schema."""
    name: str = Field(..., min_length=1, max_length=255)
    enabled: bool = True
    severities: str = "CR,MJ"  # Comma-separated: CR,MJ,MN,NA
    device_ids: Optional[str] = None
    group_ids: Optional[str] = None
    notify_email: bool = True
    notify_webhook: bool = False
    webhook_url: Optional[str] = None
    min_interval_minutes: int = 5


class NotificationSubscriptionCreate(NotificationSubscriptionBase):
    """Schema for creating a notification subscription."""
    pass


class NotificationSubscriptionUpdate(BaseModel):
    """Schema for updating a notification subscription."""
    name: Optional[str] = None
    enabled: Optional[bool] = None
    severities: Optional[str] = None
    device_ids: Optional[str] = None
    group_ids: Optional[str] = None
    notify_email: Optional[bool] = None
    notify_webhook: Optional[bool] = None
    webhook_url: Optional[str] = None
    min_interval_minutes: Optional[int] = None


class NotificationSubscriptionResponse(NotificationSubscriptionBase):
    """Schema for notification subscription response."""
    id: UUID
    user_id: UUID
    last_notification_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationLogResponse(BaseModel):
    """Schema for notification log response."""
    id: UUID
    subscription_id: UUID
    alarm_id: Optional[UUID] = None
    channel: str
    recipient: str
    subject: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationTestRequest(BaseModel):
    """Schema for testing notification delivery."""
    channel: str = "email"  # email or webhook
    recipient: Optional[str] = None  # Optional override


class NotificationStats(BaseModel):
    """Notification statistics."""
    total_subscriptions: int
    enabled_subscriptions: int
    total_sent_today: int
    total_sent_week: int
    failed_today: int
