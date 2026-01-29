"""
SQLAlchemy models for Alamo GAM.
"""
# Import Base first for model registration
from app.core.database import Base

# Import all models to ensure they're registered with SQLAlchemy
from app.models.user import User
from app.models.session import Session
from app.models.group import Group
from app.models.device import Device
from app.models.endpoint import Endpoint
from app.models.subscriber import Subscriber
from app.models.bandwidth import Bandwidth
from app.models.port import Port
from app.models.alarm import Alarm
from app.models.audit_log import AuditLog
from app.models.firmware import Firmware
from app.models.setting import Setting
from app.models.notification import NotificationSubscription, NotificationLog
from app.models.timezone import Timezone
from app.models.splynx_lookup_task import SplynxLookupTask
from app.models.config_backup import ConfigBackup

__all__ = [
    "Base",
    "User",
    "Session",
    "Group",
    "Device",
    "Endpoint",
    "Subscriber",
    "Bandwidth",
    "Port",
    "Alarm",
    "AuditLog",
    "Firmware",
    "Setting",
    "NotificationSubscription",
    "NotificationLog",
    "Timezone",
    "SplynxLookupTask",
    "ConfigBackup",
]
