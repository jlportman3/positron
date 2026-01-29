"""
Bandwidth profile API endpoints.
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.api.deps import get_db, get_current_user, require_privilege
from app.models import Bandwidth, User, Device
from app.schemas.bandwidth import (
    BandwidthCreate,
    BandwidthUpdate,
    BandwidthResponse,
    BandwidthList,
)
from app.rpc.client import GamRpcClient, GamRpcError, create_client_for_device
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=BandwidthList)
async def list_bandwidths(
    device_id: Optional[UUID] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    include_deleted: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List bandwidth profiles, optionally filtered by device."""
    query = select(Bandwidth)

    if device_id:
        query = query.where(Bandwidth.device_id == device_id)

    if not include_deleted:
        query = query.where(Bandwidth.deleted == False)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination and ordering
    query = query.order_by(Bandwidth.device_id, Bandwidth.name)
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    bandwidths = result.scalars().all()

    return BandwidthList(
        items=[BandwidthResponse(
            id=b.id,
            device_id=b.device_id,
            uid=b.uid,
            name=b.name,
            description=b.description,
            ds_bw=b.ds_bw,
            us_bw=b.us_bw,
            ds_mbps=b.ds_mbps,
            us_mbps=b.us_mbps,
            sync=b.sync,
            sync_error=b.sync_error,
            deleted=b.deleted,
            created_at=b.created_at,
            updated_at=b.updated_at,
        ) for b in bandwidths],
        total=total or 0,
        page=page,
        page_size=page_size,
    )


@router.get("/{bandwidth_id}", response_model=BandwidthResponse)
async def get_bandwidth(
    bandwidth_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a single bandwidth profile by ID."""
    result = await db.execute(
        select(Bandwidth).where(Bandwidth.id == bandwidth_id)
    )
    bandwidth = result.scalar_one_or_none()

    if not bandwidth:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bandwidth profile not found",
        )

    return BandwidthResponse(
        id=bandwidth.id,
        device_id=bandwidth.device_id,
        uid=bandwidth.uid,
        name=bandwidth.name,
        description=bandwidth.description,
        ds_bw=bandwidth.ds_bw,
        us_bw=bandwidth.us_bw,
        ds_mbps=bandwidth.ds_mbps,
        us_mbps=bandwidth.us_mbps,
        sync=bandwidth.sync,
        sync_error=bandwidth.sync_error,
        deleted=bandwidth.deleted,
        created_at=bandwidth.created_at,
        updated_at=bandwidth.updated_at,
    )


@router.post("", response_model=BandwidthResponse, status_code=status.HTTP_201_CREATED)
async def create_bandwidth(
    bandwidth_data: BandwidthCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(3)),  # Operator level
):
    """Create a new bandwidth profile.

    Note: This creates the profile in the database. To push it to the device,
    use the sync endpoint.
    """
    # Verify device exists
    device_result = await db.execute(
        select(Device).where(Device.id == bandwidth_data.device_id)
    )
    device = device_result.scalar_one_or_none()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    # Check for duplicate name on this device
    existing = await db.execute(
        select(Bandwidth).where(
            and_(
                Bandwidth.device_id == bandwidth_data.device_id,
                Bandwidth.name == bandwidth_data.name,
                Bandwidth.deleted == False,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bandwidth profile with this name already exists on this device",
        )

    bandwidth = Bandwidth(
        device_id=bandwidth_data.device_id,
        name=bandwidth_data.name,
        description=bandwidth_data.description,
        ds_bw=bandwidth_data.ds_bw,
        us_bw=bandwidth_data.us_bw,
        sync=False,  # Not yet synced to device
    )
    db.add(bandwidth)
    await db.commit()
    await db.refresh(bandwidth)

    return BandwidthResponse(
        id=bandwidth.id,
        device_id=bandwidth.device_id,
        uid=bandwidth.uid,
        name=bandwidth.name,
        description=bandwidth.description,
        ds_bw=bandwidth.ds_bw,
        us_bw=bandwidth.us_bw,
        ds_mbps=bandwidth.ds_mbps,
        us_mbps=bandwidth.us_mbps,
        sync=bandwidth.sync,
        sync_error=bandwidth.sync_error,
        deleted=bandwidth.deleted,
        created_at=bandwidth.created_at,
        updated_at=bandwidth.updated_at,
    )


@router.patch("/{bandwidth_id}", response_model=BandwidthResponse)
async def update_bandwidth(
    bandwidth_id: UUID,
    bandwidth_data: BandwidthUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(3)),  # Operator level
):
    """Update a bandwidth profile."""
    result = await db.execute(
        select(Bandwidth).where(Bandwidth.id == bandwidth_id)
    )
    bandwidth = result.scalar_one_or_none()

    if not bandwidth:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bandwidth profile not found",
        )

    # Update only provided fields
    update_data = bandwidth_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(bandwidth, field, value)

    # Mark as needing sync
    bandwidth.sync = False

    await db.commit()
    await db.refresh(bandwidth)

    return BandwidthResponse(
        id=bandwidth.id,
        device_id=bandwidth.device_id,
        uid=bandwidth.uid,
        name=bandwidth.name,
        description=bandwidth.description,
        ds_bw=bandwidth.ds_bw,
        us_bw=bandwidth.us_bw,
        ds_mbps=bandwidth.ds_mbps,
        us_mbps=bandwidth.us_mbps,
        sync=bandwidth.sync,
        sync_error=bandwidth.sync_error,
        deleted=bandwidth.deleted,
        created_at=bandwidth.created_at,
        updated_at=bandwidth.updated_at,
    )


@router.delete("/{bandwidth_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bandwidth(
    bandwidth_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(5)),  # Senior Operator level
):
    """Delete a bandwidth profile (soft delete)."""
    result = await db.execute(
        select(Bandwidth).where(Bandwidth.id == bandwidth_id)
    )
    bandwidth = result.scalar_one_or_none()

    if not bandwidth:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bandwidth profile not found",
        )

    bandwidth.deleted = True
    await db.commit()


# Device push endpoints

@router.post("/{bandwidth_id}/push")
async def push_bandwidth_to_device(
    bandwidth_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(3)),  # Operator level
):
    """Push a bandwidth profile to the device.

    Creates or updates the bandwidth profile on the GAM device.
    """
    result = await db.execute(
        select(Bandwidth).where(Bandwidth.id == bandwidth_id)
    )
    bandwidth = result.scalar_one_or_none()

    if not bandwidth:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bandwidth profile not found",
        )

    # Get device
    device_result = await db.execute(
        select(Device).where(Device.id == bandwidth.device_id)
    )
    device = device_result.scalar_one_or_none()

    if not device or not device.ip_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device not found or has no IP address",
        )

    try:
        client = await create_client_for_device(device)

        if bandwidth.uid:
            # Edit existing profile (use name as identifier)
            result = await client.edit_bandwidth_profile(
                name=bandwidth.name,
                description=bandwidth.description or "",
                ds_bw=bandwidth.ds_bw or 0,
                us_bw=bandwidth.us_bw or 0,
            )
        else:
            # Add new profile
            result = await client.add_bandwidth_profile(
                name=bandwidth.name,
                description=bandwidth.description or "",
                ds_bw=bandwidth.ds_bw or 0,
                us_bw=bandwidth.us_bw or 0,
            )

        # Save config
        await client.save_config()
        await client.close()

        # Mark as synced
        bandwidth.sync = True
        bandwidth.sync_error = None
        await db.commit()

        return {
            "status": "success",
            "message": f"Bandwidth profile '{bandwidth.name}' pushed to device {device.serial_number}",
            "result": result,
        }
    except GamRpcError as e:
        logger.error(f"RPC error pushing bandwidth: {e}")
        bandwidth.sync = False
        bandwidth.sync_error = str(e.message)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RPC error: {e.message}",
        )
    except Exception as e:
        logger.error(f"Error pushing bandwidth: {e}")
        bandwidth.sync = False
        bandwidth.sync_error = str(e)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete("/{bandwidth_id}/device")
async def delete_bandwidth_from_device(
    bandwidth_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(5)),  # Manager level
):
    """Delete a bandwidth profile from the device.

    Removes the profile from the GAM device and marks it as deleted in the database.
    """
    result = await db.execute(
        select(Bandwidth).where(Bandwidth.id == bandwidth_id)
    )
    bandwidth = result.scalar_one_or_none()

    if not bandwidth:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bandwidth profile not found",
        )

    # Get device
    device_result = await db.execute(
        select(Device).where(Device.id == bandwidth.device_id)
    )
    device = device_result.scalar_one_or_none()

    if not device or not device.ip_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device not found or has no IP address",
        )

    try:
        client = await create_client_for_device(device)

        # Delete by name
        result = await client.delete_bandwidth_profile(bandwidth.name)

        # Save config
        await client.save_config()
        await client.close()

        # Soft delete in database
        bandwidth.deleted = True
        await db.commit()

        return {
            "status": "success",
            "message": f"Bandwidth profile '{bandwidth.name}' deleted from device {device.serial_number}",
            "result": result,
        }
    except GamRpcError as e:
        logger.error(f"RPC error deleting bandwidth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RPC error: {e.message}",
        )
    except Exception as e:
        logger.error(f"Error deleting bandwidth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
