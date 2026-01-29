"""
Sessions API endpoints - manage active user sessions.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models.session import Session
from app.models.user import User
from app.api.deps import get_current_user, get_current_session

router = APIRouter(prefix="/sessions", tags=["sessions"])


class SessionResponse(BaseModel):
    id: str
    session_id: str
    user_id: str
    username: str
    ip_address: str | None
    user_agent: str | None
    privilege_level: int
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    is_current: bool = False

    class Config:
        from_attributes = True


@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_session: Session = Depends(get_current_session),
):
    """List all active sessions."""
    # Only admins (level 14+) can see all sessions
    if current_user.privilege_level < 14:
        raise HTTPException(status_code=403, detail="Insufficient privileges")

    # Get current time to filter expired sessions
    now = datetime.utcnow()

    result = await db.execute(
        select(Session)
        .options(selectinload(Session.user))
        .where(Session.expires_at > now)
        .order_by(Session.last_activity.desc())
    )
    sessions = result.scalars().all()

    return [
        SessionResponse(
            id=s.id,
            session_id=s.id,
            user_id=str(s.user_id),
            username=s.user.username if s.user else "Unknown",
            ip_address=s.ip_address,
            user_agent=s.user_agent,
            privilege_level=s.user.privilege_level if s.user else 0,
            created_at=s.created_at,
            last_activity=s.last_activity,
            expires_at=s.expires_at,
            is_current=(s.id == current_session.id if current_session else False),
        )
        for s in sessions
    ]


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_session: Session = Depends(get_current_session),
):
    """Get a session by ID."""
    # Only admins (level 14+) can view session details
    if current_user.privilege_level < 14:
        raise HTTPException(status_code=403, detail="Insufficient privileges")

    result = await db.execute(
        select(Session)
        .options(selectinload(Session.user))
        .where(Session.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse(
        id=session.id,
        session_id=session.id,
        user_id=str(session.user_id),
        username=session.user.username if session.user else "Unknown",
        ip_address=session.ip_address,
        user_agent=session.user_agent,
        privilege_level=session.user.privilege_level if session.user else 0,
        created_at=session.created_at,
        last_activity=session.last_activity,
        expires_at=session.expires_at,
        is_current=(session.id == current_session.id if current_session else False),
    )


@router.delete("/{session_id}")
async def terminate_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_session: Session = Depends(get_current_session),
):
    """Terminate a session (log out user)."""
    # Only admins (level 14+) can terminate sessions
    if current_user.privilege_level < 14:
        raise HTTPException(status_code=403, detail="Insufficient privileges")

    # Cannot terminate your own session this way
    if current_session and session_id == current_session.id:
        raise HTTPException(status_code=400, detail="Cannot terminate your own session. Use logout instead.")

    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    await db.delete(session)
    await db.commit()

    return {"message": "Session terminated successfully"}
