"""
Setting model - key-value configuration store.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Setting(Base):
    """Key-value setting store."""

    __tablename__ = "settings"

    # Primary key is the setting key
    key: Mapped[str] = mapped_column(String(255), primary_key=True)

    # Setting type for grouping (general, automation, device, etc.)
    type: Mapped[str] = mapped_column(String(64), default="general")

    # Value stored as text
    value: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(64))
    updated_by: Mapped[Optional[str]] = mapped_column(String(64))

    def __repr__(self) -> str:
        return f"<Setting {self.key}={self.value}>"


# Default settings with their keys, types, and default values
DEFAULT_SETTINGS = {
    # Device settings
    "device_minutes_considered_active": ("device", "5"),
    "device_minutes_warning_active": ("device", "2"),
    "device_config_backup_quantity": ("device", "10"),
    "device_default_rpc_username": ("device", "admin"),
    "device_default_rpc_password": ("device", ""),

    # Endpoint thresholds
    "endpoint_tca_phy_warning_level": ("endpoint", "0"),
    "endpoint_tca_phy_error_level": ("endpoint", "0"),
    "endpoint_tca_bandwidth_warning_level": ("endpoint", "800"),
    "endpoint_tca_bandwidth_error_level": ("endpoint", "300"),
    "max_coax_endpoints_warning_level": ("endpoint", "11"),
    "max_coax_endpoints_error_level": ("endpoint", "14"),

    # Polling intervals (minutes)
    "polling_endpoints_interval": ("polling", "5"),
    "polling_subscribers_interval": ("polling", "60"),
    "polling_ports_interval": ("polling", "60"),
    "polling_uptime_interval": ("polling", "5"),
    "polling_bandwidth_interval": ("polling", "60"),

    # General settings
    "login_terms": ("general", ""),
    "convert_date_with_user_timezone": ("general", "true"),
    "activate_group_access_mode": ("general", "false"),
    "api_enabled": ("general", "true"),

    # Timezone settings
    "timezone_automation": ("timezone", "false"),
    "timezone_position": ("timezone", "0"),
    "timezone_hours": ("timezone", "0"),
    "timezone_minutes": ("timezone", "0"),
    "timezone_acronym": ("timezone", ""),

    # NTP settings
    "ntp_automation": ("ntp", "false"),
    "ntp_server_1": ("ntp", ""),
    "ntp_server_2": ("ntp", ""),
    "ntp_server_3": ("ntp", ""),

    # Email settings
    "email_enable": ("email", "false"),
    "email_host_name": ("email", ""),
    "email_host_port": ("email", "587"),
    "email_host_ssl": ("email", "true"),
    "email_host_from": ("email", ""),
    "email_host_username": ("email", ""),
    "email_host_password": ("email", ""),

    # Purge settings
    "auditing_purge_delay": ("purge", "30"),
    "alarm_purge_delay": ("purge", "30"),

    # Firmware
    "firmware_upgrade_enable": ("firmware", "false"),

    # RADIUS authentication
    "radius_activate": ("radius", "false"),
    "radius_1_ip": ("radius", ""),
    "radius_1_secret": ("radius", ""),
    "radius_1_authenticator": ("radius", ""),
    "radius_1_port": ("radius", "1812"),
    "radius_2_ip": ("radius", ""),
    "radius_2_secret": ("radius", ""),
    "radius_2_authenticator": ("radius", ""),
    "radius_2_port": ("radius", "1812"),
    "radius_3_ip": ("radius", ""),
    "radius_3_secret": ("radius", ""),
    "radius_3_authenticator": ("radius", ""),
    "radius_3_port": ("radius", "1812"),
    "radius_4_ip": ("radius", ""),
    "radius_4_secret": ("radius", ""),
    "radius_4_authenticator": ("radius", ""),
    "radius_4_port": ("radius", "1812"),
    "radius_5_ip": ("radius", ""),
    "radius_5_secret": ("radius", ""),
    "radius_5_authenticator": ("radius", ""),
    "radius_5_port": ("radius", "1812"),
    "radius_session_timeout": ("radius", "30"),

    # Session / user settings
    "require_terms_acceptance": ("general", "false"),
    "enforce_strong_passwords": ("general", "false"),
    "max_session_duration": ("general", "480"),
    "default_user_timezone": ("general", "UTC"),

    # Splynx integration settings
    "splynx_api_url": ("splynx", ""),
    "splynx_api_key": ("splynx", ""),
    "splynx_api_secret": ("splynx", ""),
    "splynx_webhook_secret": ("splynx", ""),
    "splynx_auto_provision": ("splynx", "false"),
    "splynx_default_bandwidth_profile": ("splynx", "Unthrottled"),
    "splynx_default_vlan": ("splynx", "100"),
    "splynx_default_poe_mode": ("splynx", "disable"),
    "splynx_qc_ticket_assignee_id": ("splynx", ""),
    "splynx_reconciliation_time": ("splynx", "02:00"),
    "splynx_retry_duration_hours": ("splynx", "24"),

    # Privilege levels (minimum privilege level required for each feature)
    # Monitoring
    "privilege_alarms_display": ("privilege", "1"),
    "privilege_alarms_radius_test": ("privilege", "7"),
    # Services
    "privilege_subscribers_display": ("privilege", "3"),
    "privilege_subscribers_edit": ("privilege", "5"),
    "privilege_bandwidths_display": ("privilege", "3"),
    "privilege_bandwidths_edit": ("privilege", "7"),
    # Automation
    "privilege_automation_display": ("privilege", "5"),
    "privilege_automation_edit": ("privilege", "7"),
    # Devices
    "privilege_gam_display": ("privilege", "3"),
    "privilege_gam_edit": ("privilege", "7"),
    "privilege_endpoints_display": ("privilege", "3"),
    "privilege_endpoints_edit": ("privilege", "5"),
    "privilege_groups_display": ("privilege", "3"),
    "privilege_groups_edit": ("privilege", "7"),
    "privilege_timezones_display": ("privilege", "5"),
    "privilege_timezones_edit": ("privilege", "7"),
    "privilege_firmware_display": ("privilege", "5"),
    "privilege_firmware_edit": ("privilege", "9"),
    # Versions
    "privilege_versions_display": ("privilege", "5"),
    "privilege_versions_edit": ("privilege", "9"),
    # Admin
    "privilege_sessions_display": ("privilege", "7"),
    "privilege_sessions_edit": ("privilege", "9"),
    "privilege_logs_display": ("privilege", "7"),
    "privilege_users_display": ("privilege", "7"),
    "privilege_users_edit": ("privilege", "9"),
    "privilege_settings_display": ("privilege", "7"),
    "privilege_settings_edit": ("privilege", "9"),
    "privilege_auditing_display": ("privilege", "7"),
    "privilege_notifications_display": ("privilege", "5"),
    "privilege_notifications_edit": ("privilege", "7"),

    # SMTP auth toggle
    "email_require_auth": ("email", "true"),
}
