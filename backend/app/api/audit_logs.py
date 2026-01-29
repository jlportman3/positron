"""
Audit log API endpoints.
"""
from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.api.deps import get_db, get_current_user, require_privilege
from app.models import AuditLog, User
from app.schemas.audit_log import (
    AuditLogResponse,
    AuditLogList,
    AuditLogStats,
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=AuditLogList)
async def list_audit_logs(
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    username: Optional[str] = None,
    search: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(7)),  # Manager level required
):
    """List audit log entries with filtering."""
    query = select(AuditLog)

    # Apply filters
    if action:
        query = query.where(AuditLog.action == action)
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    if username:
        query = query.where(AuditLog.username.ilike(f"%{username}%"))
    if search:
        query = query.where(
            AuditLog.description.ilike(f"%{search}%") |
            AuditLog.entity_name.ilike(f"%{search}%")
        )
    if start_date:
        query = query.where(AuditLog.created_at >= start_date)
    if end_date:
        query = query.where(AuditLog.created_at <= end_date)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination and ordering
    query = query.order_by(desc(AuditLog.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    logs = result.scalars().all()

    return AuditLogList(
        items=[
            AuditLogResponse(
                id=log.id,
                user_id=log.user_id,
                username=log.username,
                ip_address=log.ip_address,
                action=log.action,
                entity_type=log.entity_type,
                entity_id=log.entity_id,
                entity_name=log.entity_name,
                description=log.description,
                old_values=log.old_values,
                new_values=log.new_values,
                created_at=log.created_at,
            )
            for log in logs
        ],
        total=total or 0,
        page=page,
        page_size=page_size,
    )


@router.get("/stats", response_model=AuditLogStats)
async def get_audit_stats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(7)),  # Manager level required
):
    """Get audit log statistics."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)

    # Total entries
    total_result = await db.execute(select(func.count(AuditLog.id)))
    total_entries = total_result.scalar() or 0

    # Entries today
    today_result = await db.execute(
        select(func.count(AuditLog.id)).where(AuditLog.created_at >= today_start)
    )
    entries_today = today_result.scalar() or 0

    # Entries this week
    week_result = await db.execute(
        select(func.count(AuditLog.id)).where(AuditLog.created_at >= week_start)
    )
    entries_this_week = week_result.scalar() or 0

    # Top users (last 7 days)
    top_users_result = await db.execute(
        select(AuditLog.username, func.count(AuditLog.id).label("count"))
        .where(AuditLog.created_at >= week_start)
        .group_by(AuditLog.username)
        .order_by(desc("count"))
        .limit(5)
    )
    top_users = [{"username": row[0], "count": row[1]} for row in top_users_result.all()]

    # Top actions (last 7 days)
    top_actions_result = await db.execute(
        select(AuditLog.action, func.count(AuditLog.id).label("count"))
        .where(AuditLog.created_at >= week_start)
        .group_by(AuditLog.action)
        .order_by(desc("count"))
        .limit(5)
    )
    top_actions = [{"action": row[0], "count": row[1]} for row in top_actions_result.all()]

    return AuditLogStats(
        total_entries=total_entries,
        entries_today=entries_today,
        entries_this_week=entries_this_week,
        top_users=top_users,
        top_actions=top_actions,
    )


@router.get("/actions")
async def get_action_types(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get list of distinct action types."""
    result = await db.execute(
        select(AuditLog.action).distinct().order_by(AuditLog.action)
    )
    actions = [row[0] for row in result.all()]
    return {"actions": actions}


@router.get("/entity-types")
async def get_entity_types(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get list of distinct entity types."""
    result = await db.execute(
        select(AuditLog.entity_type).distinct().order_by(AuditLog.entity_type)
    )
    entity_types = [row[0] for row in result.all()]
    return {"entity_types": entity_types}


@router.get("/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_privilege(7)),  # Manager level required
):
    """Get a single audit log entry."""
    result = await db.execute(
        select(AuditLog).where(AuditLog.id == log_id)
    )
    log = result.scalar_one_or_none()

    if not log:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log entry not found",
        )

    return AuditLogResponse(
        id=log.id,
        user_id=log.user_id,
        username=log.username,
        ip_address=log.ip_address,
        action=log.action,
        entity_type=log.entity_type,
        entity_id=log.entity_id,
        entity_name=log.entity_name,
        description=log.description,
        old_values=log.old_values,
        new_values=log.new_values,
        created_at=log.created_at,
    )
