"""Pydantic schemas for API request/response validation"""
from .gam import (
    GAMDeviceCreate,
    GAMDeviceUpdate,
    GAMDeviceResponse,
    GAMDeviceDiscoverRequest,
    GAMPortResponse,
)
from .user import UserResponse, Token

__all__ = [
    "GAMDeviceCreate",
    "GAMDeviceUpdate",
    "GAMDeviceResponse",
    "GAMDeviceDiscoverRequest",
    "GAMPortResponse",
    "UserResponse",
    "Token",
]
