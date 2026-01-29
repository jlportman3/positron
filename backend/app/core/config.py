"""
Application configuration using Pydantic Settings.
"""
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Alamo GAM"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "postgresql+asyncpg://alamogam:alamogam@localhost:5432/alamogam"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 1440  # 24 hours
    session_idle_timeout_minutes: int = 15

    # Device Authentication
    device_username: str = "device"
    device_password: str = "device"
    device_auth_optional: bool = True  # Allow unauthenticated announcements for legacy GAMs

    # SSH Tunnel Server
    ssh_enabled: bool = True
    ssh_host: str = "0.0.0.0"
    ssh_port: int = 2222
    ssh_host_key_path: str = "/app/data/ssh_host_key"
    ssh_port_range_start: int = 50000
    ssh_port_range_end: int = 65500

    # Polling Intervals (minutes)
    poll_endpoints_interval: int = 5
    poll_subscribers_interval: int = 60
    poll_bandwidths_interval: int = 60
    poll_ports_interval: int = 60
    poll_uptime_interval: int = 5

    # Device Communication
    device_timeout_seconds: int = 45
    device_announcement_enabled: bool = True

    # Firmware Storage
    FIRMWARE_DIR: str = "/app/firmware"
    BASE_URL: str = "http://localhost:8000"  # URL devices use to download firmware

    # Branding (white-label)
    brand_name: str = "Alamo GAM"
    brand_logo_url: Optional[str] = None
    brand_primary_color: str = "#1976d2"

    # Splynx Integration
    splynx_enabled: bool = False
    splynx_api_url: Optional[str] = None
    splynx_api_key: Optional[str] = None

    # Email Notifications
    smtp_enabled: bool = False
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None

    # Webhooks
    webhook_enabled: bool = False
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
