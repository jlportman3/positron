"""
Pydantic schemas for API request/response validation.
"""
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    SessionInfo,
)
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserList,
)
from app.schemas.device import (
    DeviceAnnouncement,
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
    DeviceBrief,
    DeviceList,
)
from app.schemas.endpoint import (
    EndpointResponse,
    EndpointBrief,
    EndpointList,
)
from app.schemas.subscriber import (
    SubscriberCreate,
    SubscriberUpdate,
    SubscriberResponse,
    SubscriberList,
)
from app.schemas.bandwidth import (
    BandwidthCreate,
    BandwidthUpdate,
    BandwidthResponse,
    BandwidthList,
)
from app.schemas.alarm import (
    AlarmResponse,
    AlarmList,
    AlarmCounts,
)

__all__ = [
    # Auth
    "LoginRequest",
    "LoginResponse",
    "SessionInfo",
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserList",
    # Device
    "DeviceAnnouncement",
    "DeviceCreate",
    "DeviceUpdate",
    "DeviceResponse",
    "DeviceBrief",
    "DeviceList",
    # Endpoint
    "EndpointResponse",
    "EndpointBrief",
    "EndpointList",
    # Subscriber
    "SubscriberCreate",
    "SubscriberUpdate",
    "SubscriberResponse",
    "SubscriberList",
    # Bandwidth
    "BandwidthCreate",
    "BandwidthUpdate",
    "BandwidthResponse",
    "BandwidthList",
    # Alarm
    "AlarmResponse",
    "AlarmList",
    "AlarmCounts",
]
