"""
Notification service for sending alarm notifications.
"""
import logging
import smtplib
import ssl
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import NotificationSubscription, NotificationLog, User, Setting, Alarm, Device

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications via email and webhook."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._email_settings = None

    async def get_email_settings(self) -> dict:
        """Load email settings from database."""
        if self._email_settings:
            return self._email_settings

        settings = {}
        result = await self.db.execute(
            select(Setting).where(Setting.type == "email")
        )
        for setting in result.scalars().all():
            settings[setting.key] = setting.value

        self._email_settings = {
            "enabled": settings.get("email_enable", "false") == "true",
            "host": settings.get("email_host_name", ""),
            "port": int(settings.get("email_host_port", "587")),
            "ssl": settings.get("email_host_ssl", "true") == "true",
            "from_address": settings.get("email_host_from", ""),
            "username": settings.get("email_host_username", ""),
            "password": settings.get("email_host_password", ""),
        }
        return self._email_settings

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
    ) -> bool:
        """Send an email notification."""
        settings = await self.get_email_settings()

        if not settings["enabled"]:
            logger.warning("Email notifications are disabled")
            return False

        if not settings["host"] or not settings["from_address"]:
            logger.error("Email settings not configured")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings["from_address"]
        msg["To"] = to

        msg.attach(MIMEText(body, "plain"))
        if html_body:
            msg.attach(MIMEText(html_body, "html"))

        try:
            if settings["ssl"]:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(settings["host"], settings["port"], context=context) as server:
                    if settings["username"] and settings["password"]:
                        server.login(settings["username"], settings["password"])
                    server.send_message(msg)
            else:
                with smtplib.SMTP(settings["host"], settings["port"]) as server:
                    server.starttls()
                    if settings["username"] and settings["password"]:
                        server.login(settings["username"], settings["password"])
                    server.send_message(msg)

            logger.info(f"Email sent to {to}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise

    async def send_webhook(
        self,
        url: str,
        payload: dict,
    ) -> bool:
        """Send a webhook notification."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                logger.info(f"Webhook sent to {url}")
                return True

        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")
            raise

    async def process_alarm(
        self,
        alarm: Alarm,
        event_type: str = "raised",  # raised, cleared, acknowledged
    ):
        """Process an alarm and send notifications to matching subscriptions."""
        # Get device info
        device = None
        if alarm.device_id:
            result = await self.db.execute(
                select(Device).where(Device.id == alarm.device_id)
            )
            device = result.scalar_one_or_none()

        # Find matching subscriptions
        result = await self.db.execute(
            select(NotificationSubscription)
            .where(NotificationSubscription.enabled == True)
        )
        subscriptions = result.scalars().all()

        for subscription in subscriptions:
            # Check severity filter
            severities = subscription.severities.split(",") if subscription.severities else []
            if alarm.severity not in severities:
                continue

            # Check device filter
            if subscription.device_ids:
                device_ids = subscription.device_ids.split(",")
                if str(alarm.device_id) not in device_ids:
                    continue

            # Check group filter
            if subscription.group_ids and device and device.group_id:
                group_ids = subscription.group_ids.split(",")
                if str(device.group_id) not in group_ids:
                    continue

            # Check rate limit
            if subscription.last_notification_at:
                min_interval = subscription.min_interval_minutes or 5
                if (datetime.utcnow() - subscription.last_notification_at).total_seconds() < min_interval * 60:
                    logger.debug(f"Rate limited: subscription {subscription.id}")
                    continue

            # Get user for email
            result = await self.db.execute(
                select(User).where(User.id == subscription.user_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                continue

            # Send notifications
            await self._send_alarm_notification(
                subscription=subscription,
                user=user,
                alarm=alarm,
                device=device,
                event_type=event_type,
            )

    async def _send_alarm_notification(
        self,
        subscription: NotificationSubscription,
        user: User,
        alarm: Alarm,
        device: Optional[Device],
        event_type: str,
    ):
        """Send alarm notification via configured channels."""
        severity_names = {
            "CR": "Critical",
            "MJ": "Major",
            "MN": "Minor",
            "NA": "Normal",
        }

        device_name = device.name or device.serial_number if device else "Unknown"
        severity_name = severity_names.get(alarm.severity, alarm.severity)

        subject = f"[{severity_name}] Alarm {event_type}: {alarm.cond_type}"
        body = f"""
Alarm Notification

Event: {event_type.upper()}
Severity: {severity_name} ({alarm.severity})
Condition: {alarm.cond_type}
Device: {device_name}
Details: {alarm.details or 'N/A'}
Time: {alarm.occurred_at}

---
Notification subscription: {subscription.name}
        """.strip()

        # Send email
        if subscription.notify_email and user.email:
            log = NotificationLog(
                subscription_id=subscription.id,
                alarm_id=alarm.id,
                channel="email",
                recipient=user.email,
                subject=subject,
            )
            try:
                await self.send_email(user.email, subject, body)
                log.status = "sent"
                log.sent_at = datetime.utcnow()
            except Exception as e:
                log.status = "failed"
                log.error_message = str(e)

            self.db.add(log)

        # Send webhook
        if subscription.notify_webhook and subscription.webhook_url:
            payload = {
                "event": f"alarm.{event_type}",
                "timestamp": datetime.utcnow().isoformat(),
                "alarm": {
                    "id": str(alarm.id),
                    "severity": alarm.severity,
                    "severity_name": severity_name,
                    "condition": alarm.cond_type,
                    "details": alarm.details,
                    "occurred_at": alarm.occurred_at.isoformat() if alarm.occurred_at else None,
                },
                "device": {
                    "id": str(device.id) if device else None,
                    "name": device_name,
                    "serial_number": device.serial_number if device else None,
                } if device else None,
            }

            log = NotificationLog(
                subscription_id=subscription.id,
                alarm_id=alarm.id,
                channel="webhook",
                recipient=subscription.webhook_url,
                subject=f"alarm.{event_type}",
                content=str(payload),
            )
            try:
                await self.send_webhook(subscription.webhook_url, payload)
                log.status = "sent"
                log.sent_at = datetime.utcnow()
            except Exception as e:
                log.status = "failed"
                log.error_message = str(e)

            self.db.add(log)

        # Update last notification time
        subscription.last_notification_at = datetime.utcnow()
        await self.db.commit()

    async def send_test_notification(
        self,
        subscription: NotificationSubscription,
        user: User,
        channel: str,
        recipient_override: Optional[str] = None,
    ):
        """Send a test notification."""
        subject = f"Test Notification from Alamo GAM"
        body = f"""
This is a test notification.

Subscription: {subscription.name}
User: {user.username}
Channel: {channel}
Time: {datetime.utcnow().isoformat()}

If you received this message, your notification settings are working correctly.
        """.strip()

        if channel == "email":
            recipient = recipient_override or user.email
            if not recipient:
                raise ValueError("No email address available")

            log = NotificationLog(
                subscription_id=subscription.id,
                channel="email",
                recipient=recipient,
                subject=subject,
            )
            try:
                await self.send_email(recipient, subject, body)
                log.status = "sent"
                log.sent_at = datetime.utcnow()
            except Exception as e:
                log.status = "failed"
                log.error_message = str(e)
                raise

            self.db.add(log)
            await self.db.commit()

        elif channel == "webhook":
            url = recipient_override or subscription.webhook_url
            if not url:
                raise ValueError("No webhook URL configured")

            payload = {
                "event": "test",
                "timestamp": datetime.utcnow().isoformat(),
                "message": "This is a test notification",
                "subscription": {
                    "id": str(subscription.id),
                    "name": subscription.name,
                },
            }

            log = NotificationLog(
                subscription_id=subscription.id,
                channel="webhook",
                recipient=url,
                subject="test",
                content=str(payload),
            )
            try:
                await self.send_webhook(url, payload)
                log.status = "sent"
                log.sent_at = datetime.utcnow()
            except Exception as e:
                log.status = "failed"
                log.error_message = str(e)
                raise

            self.db.add(log)
            await self.db.commit()

        else:
            raise ValueError(f"Unknown channel: {channel}")
