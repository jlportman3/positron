"""
Notification API endpoints.
"""
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete

from app.api.deps import get_db, get_current_user
from app.models import User, NotificationSubscription, NotificationLog
from app.schemas.notification import (
    NotificationSubscriptionCreate,
    NotificationSubscriptionUpdate,
    NotificationSubscriptionResponse,
    NotificationLogResponse,
    NotificationTestRequest,
    NotificationStats,
)
from app.services.notification_service import NotificationService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=List[NotificationSubscriptionResponse])
async def list_subscriptions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List notification subscriptions for the current user."""
    result = await db.execute(
        select(NotificationSubscription)
        .where(NotificationSubscription.user_id == user.id)
        .order_by(NotificationSubscription.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=NotificationSubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    data: NotificationSubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new notification subscription."""
    subscription = NotificationSubscription(
        user_id=user.id,
        name=data.name,
        enabled=data.enabled,
        severities=data.severities,
        device_ids=data.device_ids,
        group_ids=data.group_ids,
        notify_email=data.notify_email,
        notify_webhook=data.notify_webhook,
        webhook_url=data.webhook_url,
        min_interval_minutes=data.min_interval_minutes,
    )
    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)
    logger.info(f"Created notification subscription {subscription.id} for user {user.username}")
    return subscription


@router.get("/stats", response_model=NotificationStats)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get notification statistics for the current user."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)

    # Count subscriptions
    total_subs = await db.execute(
        select(func.count(NotificationSubscription.id))
        .where(NotificationSubscription.user_id == user.id)
    )
    enabled_subs = await db.execute(
        select(func.count(NotificationSubscription.id))
        .where(NotificationSubscription.user_id == user.id)
        .where(NotificationSubscription.enabled == True)
    )

    # Get user's subscription IDs for log queries
    sub_result = await db.execute(
        select(NotificationSubscription.id)
        .where(NotificationSubscription.user_id == user.id)
    )
    sub_ids = [s for s in sub_result.scalars().all()]

    # Count notifications
    sent_today = 0
    sent_week = 0
    failed_today = 0

    if sub_ids:
        sent_today_result = await db.execute(
            select(func.count(NotificationLog.id))
            .where(NotificationLog.subscription_id.in_(sub_ids))
            .where(NotificationLog.created_at >= today_start)
            .where(NotificationLog.status == "sent")
        )
        sent_today = sent_today_result.scalar() or 0

        sent_week_result = await db.execute(
            select(func.count(NotificationLog.id))
            .where(NotificationLog.subscription_id.in_(sub_ids))
            .where(NotificationLog.created_at >= week_start)
            .where(NotificationLog.status == "sent")
        )
        sent_week = sent_week_result.scalar() or 0

        failed_today_result = await db.execute(
            select(func.count(NotificationLog.id))
            .where(NotificationLog.subscription_id.in_(sub_ids))
            .where(NotificationLog.created_at >= today_start)
            .where(NotificationLog.status == "failed")
        )
        failed_today = failed_today_result.scalar() or 0

    return NotificationStats(
        total_subscriptions=total_subs.scalar() or 0,
        enabled_subscriptions=enabled_subs.scalar() or 0,
        total_sent_today=sent_today,
        total_sent_week=sent_week,
        failed_today=failed_today,
    )


@router.get("/logs", response_model=List[NotificationLogResponse])
async def list_logs(
    page: int = 1,
    page_size: int = 50,
    subscription_id: Optional[UUID] = None,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List notification logs for the current user."""
    # Get user's subscription IDs
    sub_result = await db.execute(
        select(NotificationSubscription.id)
        .where(NotificationSubscription.user_id == user.id)
    )
    sub_ids = [s for s in sub_result.scalars().all()]

    if not sub_ids:
        return []

    query = select(NotificationLog).where(NotificationLog.subscription_id.in_(sub_ids))

    if subscription_id:
        query = query.where(NotificationLog.subscription_id == subscription_id)
    if status_filter:
        query = query.where(NotificationLog.status == status_filter)

    query = query.order_by(NotificationLog.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{subscription_id}", response_model=NotificationSubscriptionResponse)
async def get_subscription(
    subscription_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a specific notification subscription."""
    result = await db.execute(
        select(NotificationSubscription)
        .where(NotificationSubscription.id == subscription_id)
        .where(NotificationSubscription.user_id == user.id)
    )
    subscription = result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return subscription


@router.patch("/{subscription_id}", response_model=NotificationSubscriptionResponse)
async def update_subscription(
    subscription_id: UUID,
    data: NotificationSubscriptionUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update a notification subscription."""
    result = await db.execute(
        select(NotificationSubscription)
        .where(NotificationSubscription.id == subscription_id)
        .where(NotificationSubscription.user_id == user.id)
    )
    subscription = result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(subscription, field, value)

    await db.commit()
    await db.refresh(subscription)
    logger.info(f"Updated notification subscription {subscription_id}")
    return subscription


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(
    subscription_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a notification subscription."""
    result = await db.execute(
        select(NotificationSubscription)
        .where(NotificationSubscription.id == subscription_id)
        .where(NotificationSubscription.user_id == user.id)
    )
    subscription = result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    await db.delete(subscription)
    await db.commit()
    logger.info(f"Deleted notification subscription {subscription_id}")


@router.post("/{subscription_id}/test")
async def test_notification(
    subscription_id: UUID,
    data: NotificationTestRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Send a test notification."""
    result = await db.execute(
        select(NotificationSubscription)
        .where(NotificationSubscription.id == subscription_id)
        .where(NotificationSubscription.user_id == user.id)
    )
    subscription = result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    # Get notification service
    notification_service = NotificationService(db)

    try:
        await notification_service.send_test_notification(
            subscription=subscription,
            user=user,
            channel=data.channel,
            recipient_override=data.recipient,
        )
        return {"message": f"Test {data.channel} notification sent successfully"}
    except Exception as e:
        logger.error(f"Failed to send test notification: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send test notification: {str(e)}"
        )
