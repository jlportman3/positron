"""
Settings API endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, get_current_user, require_privilege
from app.models import Setting, User
from app.models.setting import DEFAULT_SETTINGS
from app.schemas.setting import (
    SettingResponse,
    SettingUpdate,
    SettingsBulkUpdate,
    SettingsList,
    SettingsByType,
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


async def ensure_default_settings(db: AsyncSession):
    """Ensure all default settings exist in the database."""
    for key, (setting_type, default_value) in DEFAULT_SETTINGS.items():
        result = await db.execute(select(Setting).where(Setting.key == key))
        if not result.scalar_one_or_none():
            setting = Setting(key=key, type=setting_type, value=default_value)
            db.add(setting)
    await db.commit()


@router.get("", response_model=SettingsList)
async def list_settings(
    type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all settings, optionally filtered by type."""
    # Ensure defaults exist
    await ensure_default_settings(db)

    query = select(Setting).order_by(Setting.type, Setting.key)
    if type:
        query = query.where(Setting.type == type)

    result = await db.execute(query)
    settings = result.scalars().all()

    return SettingsList(
        items=[
            SettingResponse(
                key=s.key,
                type=s.type,
                value=s.value,
                created_at=s.created_at,
                updated_at=s.updated_at,
                created_by=s.created_by,
                updated_by=s.updated_by,
            )
            for s in settings
        ],
        total=len(settings),
    )


@router.get("/by-type", response_model=SettingsByType)
async def get_settings_by_type(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get all settings organized by type."""
    # Ensure defaults exist
    await ensure_default_settings(db)

    result = await db.execute(select(Setting).order_by(Setting.key))
    settings = result.scalars().all()

    # Group by type
    grouped: dict = {
        "device": [],
        "endpoint": [],
        "polling": [],
        "general": [],
        "timezone": [],
        "ntp": [],
        "email": [],
        "purge": [],
        "firmware": [],
    }

    for s in settings:
        response = SettingResponse(
            key=s.key,
            type=s.type,
            value=s.value,
            created_at=s.created_at,
            updated_at=s.updated_at,
            created_by=s.created_by,
            updated_by=s.updated_by,
        )
        if s.type in grouped:
            grouped[s.type].append(response)
        else:
            grouped["general"].append(response)

    return SettingsByType(**grouped)


@router.get("/{key}", response_model=SettingResponse)
async def get_setting(
    key: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a single setting by key."""
    result = await db.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()

    if not setting:
        # Check if it's a known default
        if key in DEFAULT_SETTINGS:
            setting_type, default_value = DEFAULT_SETTINGS[key]
            setting = Setting(key=key, type=setting_type, value=default_value)
            db.add(setting)
            await db.commit()
            await db.refresh(setting)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting '{key}' not found",
            )

    return SettingResponse(
        key=setting.key,
        type=setting.type,
        value=setting.value,
        created_at=setting.created_at,
        updated_at=setting.updated_at,
        created_by=setting.created_by,
        updated_by=setting.updated_by,
    )


@router.put("/{key}", response_model=SettingResponse)
async def update_setting(
    key: str,
    update: SettingUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(7)),  # Manager level
):
    """Update a single setting."""
    result = await db.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()

    if not setting:
        # Create new setting if it doesn't exist
        if key in DEFAULT_SETTINGS:
            setting_type, _ = DEFAULT_SETTINGS[key]
        else:
            setting_type = "general"

        setting = Setting(
            key=key,
            type=setting_type,
            value=update.value,
            created_by=user.username,
            updated_by=user.username,
        )
        db.add(setting)
    else:
        setting.value = update.value
        setting.updated_by = user.username

    await db.commit()
    await db.refresh(setting)

    logger.info(f"Setting '{key}' updated by {user.username}")

    return SettingResponse(
        key=setting.key,
        type=setting.type,
        value=setting.value,
        created_at=setting.created_at,
        updated_at=setting.updated_at,
        created_by=setting.created_by,
        updated_by=setting.updated_by,
    )


@router.post("/bulk", response_model=SettingsList)
async def bulk_update_settings(
    bulk_update: SettingsBulkUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(7)),  # Manager level
):
    """Update multiple settings at once."""
    updated_settings = []

    for key, value in bulk_update.settings.items():
        result = await db.execute(select(Setting).where(Setting.key == key))
        setting = result.scalar_one_or_none()

        if not setting:
            # Create new setting
            if key in DEFAULT_SETTINGS:
                setting_type, _ = DEFAULT_SETTINGS[key]
            else:
                setting_type = "general"

            setting = Setting(
                key=key,
                type=setting_type,
                value=value,
                created_by=user.username,
                updated_by=user.username,
            )
            db.add(setting)
        else:
            setting.value = value
            setting.updated_by = user.username

        updated_settings.append(setting)

    await db.commit()

    # Refresh all settings
    for setting in updated_settings:
        await db.refresh(setting)

    logger.info(f"Bulk update of {len(updated_settings)} settings by {user.username}")

    return SettingsList(
        items=[
            SettingResponse(
                key=s.key,
                type=s.type,
                value=s.value,
                created_at=s.created_at,
                updated_at=s.updated_at,
                created_by=s.created_by,
                updated_by=s.updated_by,
            )
            for s in updated_settings
        ],
        total=len(updated_settings),
    )


@router.post("/reset-defaults")
async def reset_to_defaults(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(9)),  # Admin level
):
    """Reset all settings to their default values."""
    reset_count = 0

    for key, (setting_type, default_value) in DEFAULT_SETTINGS.items():
        result = await db.execute(select(Setting).where(Setting.key == key))
        setting = result.scalar_one_or_none()

        if setting:
            setting.value = default_value
            setting.updated_by = user.username
        else:
            setting = Setting(
                key=key,
                type=setting_type,
                value=default_value,
                created_by=user.username,
                updated_by=user.username,
            )
            db.add(setting)
        reset_count += 1

    await db.commit()

    logger.info(f"Settings reset to defaults by {user.username}")

    return {
        "status": "success",
        "message": f"Reset {reset_count} settings to defaults",
    }


@router.post("/test-email")
async def test_email(
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(7)),
):
    """Send a test email using current SMTP settings."""
    import smtplib
    from email.mime.text import MIMEText

    to_address = body.get("to", "")
    if not to_address:
        raise HTTPException(status_code=400, detail="Recipient address required")

    # Load current SMTP settings from DB
    settings_keys = [
        "email_host_name", "email_host_port", "email_host_ssl",
        "email_host_from", "email_host_username", "email_host_password",
        "email_require_auth",
    ]
    result = await db.execute(
        select(Setting).where(Setting.key.in_(settings_keys))
    )
    settings_map = {s.key: s.value for s in result.scalars().all()}

    host = settings_map.get("email_host_name", "")
    port = int(settings_map.get("email_host_port", "587"))
    use_ssl = settings_map.get("email_host_ssl", "true") == "true"
    from_addr = settings_map.get("email_host_from", "")
    require_auth = settings_map.get("email_require_auth", "true") == "true"
    username = settings_map.get("email_host_username", "")
    password = settings_map.get("email_host_password", "")

    if not host:
        raise HTTPException(status_code=400, detail="SMTP host not configured")
    if not from_addr:
        raise HTTPException(status_code=400, detail="From address not configured")

    msg = MIMEText("This is a test email from Alamo GAM management system.")
    msg["Subject"] = "Alamo GAM - Test Email"
    msg["From"] = from_addr
    msg["To"] = to_address

    try:
        if use_ssl and port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=10)
        else:
            server = smtplib.SMTP(host, port, timeout=10)
            if use_ssl:
                server.starttls()
        if require_auth and username:
            server.login(username, password)
        server.sendmail(from_addr, [to_address], msg.as_string())
        server.quit()
        return {"status": "success", "message": f"Test email sent to {to_address}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
