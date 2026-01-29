"""
Group API endpoints.
"""
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_current_user, require_privilege
from app.models import Group, User, Device
from app.schemas.group import (
    GroupCreate,
    GroupUpdate,
    GroupResponse,
    GroupList,
    GroupTree,
    GroupDeviceAssignment,
    GroupDeviceResponse,
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def build_group_response(group: Group, parent_name: Optional[str] = None) -> GroupResponse:
    """Build GroupResponse from Group model."""
    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        parent_id=group.parent_id,
        parent_name=parent_name,
        device_count=len(group.devices) if group.devices else 0,
        child_count=len(group.children) if group.children else 0,
        created_at=group.created_at,
        updated_at=group.updated_at,
        created_by=group.created_by,
        updated_by=group.updated_by,
    )


@router.get("", response_model=GroupList)
async def list_groups(
    parent_id: Optional[UUID] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List groups, optionally filtered by parent."""
    query = select(Group).options(
        selectinload(Group.devices),
        selectinload(Group.children),
        selectinload(Group.parent),
    )

    if parent_id:
        query = query.where(Group.parent_id == parent_id)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination and ordering
    query = query.order_by(Group.name)
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    groups = result.scalars().all()

    return GroupList(
        items=[
            build_group_response(
                g,
                parent_name=g.parent.name if g.parent else None
            )
            for g in groups
        ],
        total=total or 0,
        page=page,
        page_size=page_size,
    )


@router.get("/tree", response_model=List[GroupTree])
async def get_group_tree(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get hierarchical group tree starting from root groups."""
    # Get all groups with relationships loaded
    result = await db.execute(
        select(Group).options(
            selectinload(Group.devices),
            selectinload(Group.children).selectinload(Group.devices),
        ).where(Group.parent_id == None)
    )
    root_groups = result.scalars().all()

    async def build_tree(group: Group) -> GroupTree:
        """Recursively build tree node."""
        # Load children if not already loaded
        children = []
        if group.children:
            for child in group.children:
                # Reload child with full relationships
                child_result = await db.execute(
                    select(Group).options(
                        selectinload(Group.devices),
                        selectinload(Group.children),
                    ).where(Group.id == child.id)
                )
                child_full = child_result.scalar_one_or_none()
                if child_full:
                    children.append(await build_tree(child_full))

        return GroupTree(
            id=group.id,
            name=group.name,
            description=group.description,
            parent_id=group.parent_id,
            device_count=len(group.devices) if group.devices else 0,
            children=children,
        )

    return [await build_tree(g) for g in root_groups]


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a single group by ID."""
    result = await db.execute(
        select(Group).options(
            selectinload(Group.devices),
            selectinload(Group.children),
            selectinload(Group.parent),
        ).where(Group.id == group_id)
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    return build_group_response(
        group,
        parent_name=group.parent.name if group.parent else None
    )


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_data: GroupCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(5)),  # Manager level
):
    """Create a new group."""
    # Check for duplicate name
    existing = await db.execute(
        select(Group).where(Group.name == group_data.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Group with this name already exists",
        )

    # Verify parent exists if specified
    if group_data.parent_id:
        parent_result = await db.execute(
            select(Group).where(Group.id == group_data.parent_id)
        )
        if not parent_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent group not found",
            )

    group = Group(
        name=group_data.name,
        description=group_data.description,
        parent_id=group_data.parent_id,
        created_by=user.username,
        updated_by=user.username,
    )
    db.add(group)
    await db.commit()

    # Reload with relationships to avoid lazy loading in build_group_response
    result = await db.execute(
        select(Group).options(
            selectinload(Group.devices),
            selectinload(Group.children),
        ).where(Group.id == group.id)
    )
    group = result.scalar_one()

    return build_group_response(group)


@router.patch("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: UUID,
    group_data: GroupUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(5)),  # Manager level
):
    """Update a group."""
    result = await db.execute(
        select(Group).options(
            selectinload(Group.devices),
            selectinload(Group.children),
            selectinload(Group.parent),
        ).where(Group.id == group_id)
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    # Check for name conflict if name is being changed
    if group_data.name and group_data.name != group.name:
        existing = await db.execute(
            select(Group).where(
                and_(Group.name == group_data.name, Group.id != group_id)
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Group with this name already exists",
            )

    # Verify parent exists and prevent circular reference
    if group_data.parent_id is not None:
        if group_data.parent_id == group_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Group cannot be its own parent",
            )
        if group_data.parent_id:
            parent_result = await db.execute(
                select(Group).where(Group.id == group_data.parent_id)
            )
            if not parent_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent group not found",
                )

    # Update fields
    update_data = group_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(group, field, value)
    group.updated_by = user.username

    await db.commit()
    await db.refresh(group)

    # Reload with relationships
    result = await db.execute(
        select(Group).options(
            selectinload(Group.devices),
            selectinload(Group.children),
            selectinload(Group.parent),
        ).where(Group.id == group_id)
    )
    group = result.scalar_one()

    return build_group_response(
        group,
        parent_name=group.parent.name if group.parent else None
    )


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(7)),  # Senior Manager level
):
    """Delete a group."""
    result = await db.execute(
        select(Group).options(
            selectinload(Group.devices),
            selectinload(Group.children),
        ).where(Group.id == group_id)
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    # Check if group has devices
    if group.devices:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete group with {len(group.devices)} device(s). Remove devices first.",
        )

    # Check if group has children
    if group.children:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete group with {len(group.children)} subgroup(s). Remove subgroups first.",
        )

    await db.delete(group)
    await db.commit()


# Device assignment endpoints

@router.get("/{group_id}/devices", response_model=List[GroupDeviceResponse])
async def get_group_devices(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get devices in a group."""
    result = await db.execute(
        select(Group).options(selectinload(Group.devices)).where(Group.id == group_id)
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    return [
        GroupDeviceResponse(
            id=d.id,
            serial_number=d.serial_number,
            name=d.name,
            is_online=d.is_online,
        )
        for d in group.devices
    ]


@router.post("/{group_id}/devices")
async def assign_devices_to_group(
    group_id: UUID,
    assignment: GroupDeviceAssignment,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(5)),  # Manager level
):
    """Assign devices to a group."""
    result = await db.execute(
        select(Group).where(Group.id == group_id)
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    # Update devices
    for device_id in assignment.device_ids:
        device_result = await db.execute(
            select(Device).where(Device.id == device_id)
        )
        device = device_result.scalar_one_or_none()
        if device:
            device.group_id = group_id

    await db.commit()

    return {
        "status": "success",
        "message": f"Assigned {len(assignment.device_ids)} device(s) to group '{group.name}'",
    }


@router.delete("/{group_id}/devices/{device_id}")
async def remove_device_from_group(
    group_id: UUID,
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(5)),  # Manager level
):
    """Remove a device from a group."""
    result = await db.execute(
        select(Device).where(
            and_(Device.id == device_id, Device.group_id == group_id)
        )
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found in this group",
        )

    device.group_id = None
    await db.commit()

    return {
        "status": "success",
        "message": f"Removed device '{device.serial_number}' from group",
    }
