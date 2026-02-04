"""
API routers for Alamo GAM.
"""
from fastapi import APIRouter

from app.api import auth, devices, announcement, users, endpoints, subscribers, alarms, ports, bandwidths, firmware, groups, settings, audit_logs, dashboard, notifications, export, timezones, sessions, splynx, config_backups, subscriber_import, health

# Main API router
api_router = APIRouter()

# Include all routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(announcement.router, tags=["Device Announcement"])
api_router.include_router(devices.router, prefix="/devices", tags=["Devices"])
api_router.include_router(endpoints.router, prefix="/endpoints", tags=["Endpoints"])
api_router.include_router(subscribers.router, prefix="/subscribers", tags=["Subscribers"])
api_router.include_router(alarms.router, prefix="/alarms", tags=["Alarms"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(ports.router, prefix="/ports", tags=["Ports"])
api_router.include_router(bandwidths.router, prefix="/bandwidths", tags=["Bandwidth Profiles"])
api_router.include_router(firmware.router, prefix="/firmware", tags=["Firmware"])
api_router.include_router(groups.router, prefix="/groups", tags=["Groups"])
api_router.include_router(settings.router, prefix="/settings", tags=["Settings"])
api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["Audit Logs"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(export.router, prefix="/export", tags=["Export"])
api_router.include_router(timezones.router, tags=["Timezones"])
api_router.include_router(sessions.router, tags=["Sessions"])
api_router.include_router(splynx.router, tags=["Splynx Integration"])
api_router.include_router(config_backups.router, prefix="/config-backups", tags=["Config Backups"])
api_router.include_router(subscriber_import.router, prefix="/subscriber-import", tags=["Subscriber Import"])
api_router.include_router(health.router, prefix="/health", tags=["Health Monitoring"])
