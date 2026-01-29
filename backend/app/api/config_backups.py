"""
Configuration backup API.

Handles device config backup, history, and restore operations.
Uses JSON-RPC download_config/upload_config for device communication.
"""
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete

from app.api.deps import get_db, get_current_user, require_privilege
from app.models import User, Device, Setting
from app.models.config_backup import ConfigBackup
from app.rpc.client import create_client_for_device

router = APIRouter()


@router.post("/devices/{device_id}/config-backup")
async def create_config_backup(
    device_id: UUID,
    config_type: str = Query("runningConfig", description="runningConfig or startupConfig"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(5)),
):
    """Trigger a config backup from a device via JSON-RPC."""
    device_result = await db.execute(select(Device).where(Device.id == device_id))
    device = device_result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Download config from device
    try:
        client = await create_client_for_device(device)
        config_content = await client.download_config(source_type=config_type)
        await client.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download config: {str(e)}")

    if not config_content:
        raise HTTPException(status_code=500, detail="Device returned empty config")

    # Get next version number
    result = await db.execute(
        select(func.coalesce(func.max(ConfigBackup.version_number), 0))
        .where(ConfigBackup.device_id == device_id)
    )
    next_version = result.scalar() + 1

    # Create backup record
    backup = ConfigBackup(
        device_id=device_id,
        version_number=next_version,
        config_content=config_content if isinstance(config_content, str) else str(config_content),
        config_type=config_type,
        created_by=user.username,
    )
    db.add(backup)

    # Auto-prune old backups
    max_result = await db.execute(
        select(Setting).where(Setting.key == "device_config_backup_quantity")
    )
    max_setting = max_result.scalar_one_or_none()
    max_backups = int(max_setting.value) if max_setting and max_setting.value else 10

    # Count existing backups for this device
    count_result = await db.execute(
        select(func.count()).where(ConfigBackup.device_id == device_id)
    )
    current_count = count_result.scalar()

    # Delete oldest if over limit (account for the one we just added)
    if current_count >= max_backups:
        excess = current_count - max_backups + 1
        oldest = await db.execute(
            select(ConfigBackup.id)
            .where(ConfigBackup.device_id == device_id)
            .order_by(ConfigBackup.version_number.asc())
            .limit(excess)
        )
        old_ids = [row[0] for row in oldest.all()]
        if old_ids:
            await db.execute(
                delete(ConfigBackup).where(ConfigBackup.id.in_(old_ids))
            )

    await db.commit()
    await db.refresh(backup)

    return {
        "id": str(backup.id),
        "version_number": backup.version_number,
        "config_type": backup.config_type,
        "created_at": backup.created_at.isoformat(),
        "created_by": backup.created_by,
        "message": f"Config backup v{backup.version_number} created",
    }


@router.get("/devices/{device_id}/config-backups")
async def list_config_backups(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all config backups for a device."""
    device_result = await db.execute(select(Device).where(Device.id == device_id))
    if not device_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Device not found")

    result = await db.execute(
        select(ConfigBackup)
        .where(ConfigBackup.device_id == device_id)
        .order_by(ConfigBackup.version_number.desc())
    )
    backups = result.scalars().all()

    return {
        "items": [
            {
                "id": str(b.id),
                "version_number": b.version_number,
                "config_type": b.config_type,
                "created_at": b.created_at.isoformat() if b.created_at else None,
                "created_by": b.created_by,
                "size": len(b.config_content) if b.config_content else 0,
            }
            for b in backups
        ],
        "total": len(backups),
    }


@router.get("/config-backups/{backup_id}/content")
async def get_config_backup_content(
    backup_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get the full config content of a backup."""
    result = await db.execute(
        select(ConfigBackup).where(ConfigBackup.id == backup_id)
    )
    backup = result.scalar_one_or_none()
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")

    return {
        "id": str(backup.id),
        "device_id": str(backup.device_id),
        "version_number": backup.version_number,
        "config_type": backup.config_type,
        "config_content": backup.config_content,
        "created_at": backup.created_at.isoformat() if backup.created_at else None,
        "created_by": backup.created_by,
    }


@router.post("/config-backups/{backup_id}/restore")
async def restore_config_backup(
    backup_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(7)),
):
    """Restore a config backup to its device via JSON-RPC upload_config."""
    result = await db.execute(
        select(ConfigBackup).where(ConfigBackup.id == backup_id)
    )
    backup = result.scalar_one_or_none()
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")

    device_result = await db.execute(
        select(Device).where(Device.id == backup.device_id)
    )
    device = device_result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    try:
        client = await create_client_for_device(device)
        result = await client.upload_config(backup.config_content)
        await client.close()

        return {
            "message": f"Config v{backup.version_number} restored to {device.serial_number}",
            "device_id": str(device.id),
            "version_number": backup.version_number,
            "result": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restore config: {str(e)}")


@router.delete("/config-backups/{backup_id}")
async def delete_config_backup(
    backup_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(7)),
):
    """Delete a config backup."""
    result = await db.execute(
        select(ConfigBackup).where(ConfigBackup.id == backup_id)
    )
    backup = result.scalar_one_or_none()
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")

    await db.delete(backup)
    await db.commit()

    return {"message": "Config backup deleted"}
