"""
Port API endpoints.
"""
import logging
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.deps import get_db, get_current_user, require_privilege
from app.models import Port, User, Device
from app.schemas.port import PortResponse, PortList, PortUpdate, PortWithDevice
from app.rpc.client import create_client_for_device, GamRpcError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=PortList)
async def list_ports(
    device_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List ports, optionally filtered by device."""
    query = select(Port)

    if device_id:
        query = query.where(Port.device_id == device_id)

    query = query.order_by(Port.device_id, Port.position, Port.key)

    result = await db.execute(query)
    ports = result.scalars().all()

    # Get total count
    count_query = select(func.count()).select_from(Port)
    if device_id:
        count_query = count_query.where(Port.device_id == device_id)
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    return PortList(
        items=[PortResponse.model_validate(p) for p in ports],
        total=total or 0,
        device_id=device_id,
    )


@router.get("/all", response_model=list[PortWithDevice])
async def list_all_ports(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    link: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all ports with device info, for main ports page."""
    query = select(Port, Device.name, Device.serial_number).join(Device, Port.device_id == Device.id)

    if link is not None:
        query = query.where(Port.link == link)

    if search:
        query = query.where(
            Port.key.ilike(f"%{search}%") |
            Device.name.ilike(f"%{search}%") |
            Device.serial_number.ilike(f"%{search}%")
        )

    query = query.order_by(Device.name, Port.position, Port.key)
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    rows = result.all()

    return [
        PortWithDevice(
            **PortResponse.model_validate(row[0]).model_dump(),
            device_name=row[1],
            device_serial=row[2],
        )
        for row in rows
    ]


@router.get("/{port_id}", response_model=PortResponse)
async def get_port(
    port_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a single port by ID."""
    result = await db.execute(
        select(Port).where(Port.id == port_id)
    )
    port = result.scalar_one_or_none()

    if not port:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Port not found",
        )

    return PortResponse.model_validate(port)


@router.patch("/{port_id}", response_model=PortResponse)
async def update_port(
    port_id: UUID,
    data: PortUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(3)),  # Operator level
):
    """Update a port's configuration in database."""
    result = await db.execute(
        select(Port).where(Port.id == port_id)
    )
    port = result.scalar_one_or_none()

    if not port:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Port not found",
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(port, field, value)

    await db.commit()
    await db.refresh(port)

    return PortResponse.model_validate(port)


@router.post("/{port_id}/push")
async def push_port_config(
    port_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(3)),  # Operator level
):
    """Push port configuration to device.

    Sends the port configuration to the GAM device via JSON-RPC.
    """
    result = await db.execute(
        select(Port).where(Port.id == port_id)
    )
    port = result.scalar_one_or_none()

    if not port:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Port not found",
        )

    # Get device
    device_result = await db.execute(
        select(Device).where(Device.id == port.device_id)
    )
    device = device_result.scalar_one_or_none()

    if not device or not device.ip_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device not found or has no IP address",
        )

    try:
        client = await create_client_for_device(device)

        # Determine port index from port key (e.g., "G.hn 1/4" -> index 4)
        port_index = port.position or 1

        result = await client.set_port_config(
            port_index=port_index,
            enabled=port.admin_status == "up" if port.admin_status else None,
            description=port.description,
        )

        # Save config
        await client.save_config()
        await client.close()

        return {
            "status": "success",
            "message": f"Port config pushed to device {device.serial_number}",
            "result": result,
        }
    except GamRpcError as e:
        logger.error(f"RPC error pushing port config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RPC error: {e.message}",
        )
    except Exception as e:
        logger.error(f"Error pushing port config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/{port_id}/ghn-config")
async def push_ghn_port_config(
    port_id: UUID,
    enabled: Optional[bool] = None,
    power_back_off: Optional[int] = None,
    force_master: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(3)),  # Operator level
):
    """Push G.hn specific port configuration to device.

    Args:
        enabled: Enable/disable G.hn on this port
        power_back_off: Power back-off level (0-15)
        force_master: Force this port as domain master
    """
    result = await db.execute(
        select(Port).where(Port.id == port_id)
    )
    port = result.scalar_one_or_none()

    if not port:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Port not found",
        )

    # Get device
    device_result = await db.execute(
        select(Device).where(Device.id == port.device_id)
    )
    device = device_result.scalar_one_or_none()

    if not device or not device.ip_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device not found or has no IP address",
        )

    try:
        client = await create_client_for_device(device)

        # Use the port key as the interface index
        port_if_index = port.key or f"G.hn 1/{port.position or 1}"

        result = await client.set_ghn_port_config(
            port_if_index=port_if_index,
            enabled=enabled,
            power_back_off=power_back_off,
            force_master=force_master,
        )

        # Save config
        await client.save_config()
        await client.close()

        return {
            "status": "success",
            "message": f"G.hn port config pushed to device {device.serial_number}",
            "result": result,
        }
    except GamRpcError as e:
        logger.error(f"RPC error pushing G.hn port config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RPC error: {e.message}",
        )
    except Exception as e:
        logger.error(f"Error pushing G.hn port config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
