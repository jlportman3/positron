"""
Authentication API endpoints.
"""
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.security import verify_password, generate_session_id, PRIVILEGE_LEVELS
from app.core.database import async_session_maker
from app.models import User, Session
from app.models.setting import Setting
from app.schemas.auth import LoginRequest, LoginResponse, SessionInfo
from app.api.deps import get_db, get_current_session, get_current_user

logger = logging.getLogger(__name__)


async def _radius_authenticate(username: str, password: str, db: AsyncSession) -> bool:
    """Attempt RADIUS authentication against configured servers. Returns True if authenticated."""
    try:
        from pyrad.client import Client
        from pyrad.dictionary import Dictionary
        from pyrad import packet
        import io
    except ImportError:
        logger.warning("pyrad not installed, skipping RADIUS auth")
        return False

    # Minimal RADIUS dictionary
    RADIUS_DICT = """
ATTRIBUTE	User-Name		1	string
ATTRIBUTE	User-Password		2	string
ATTRIBUTE	NAS-Identifier		32	string
"""

    for i in range(1, 6):
        ip_result = await db.execute(select(Setting).where(Setting.key == f"radius_{i}_ip"))
        ip_setting = ip_result.scalar_one_or_none()
        if not ip_setting or not ip_setting.value:
            continue

        secret_result = await db.execute(select(Setting).where(Setting.key == f"radius_{i}_secret"))
        secret_setting = secret_result.scalar_one_or_none()
        if not secret_setting or not secret_setting.value:
            continue

        port_result = await db.execute(select(Setting).where(Setting.key == f"radius_{i}_port"))
        port_setting = port_result.scalar_one_or_none()
        port = int(port_setting.value) if port_setting and port_setting.value else 1812

        try:
            srv = Client(
                server=ip_setting.value,
                secret=secret_setting.value.encode(),
                dict=Dictionary(io.StringIO(RADIUS_DICT)),
                authport=port,
                acctport=port + 1,
            )
            srv.timeout = 5

            req = srv.CreateAuthPacket(code=packet.AccessRequest, User_Name=username)
            req["User-Password"] = req.PwCrypt(password)

            reply = srv.SendPacket(req)
            if reply.code == packet.AccessAccept:
                return True
        except Exception as e:
            logger.warning(f"RADIUS server {i} ({ip_setting.value}) failed: {e}")
            continue

    return False

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    response: Response,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Login with username and password.

    Returns session info and sets session cookie.
    """
    # Find user
    result = await db.execute(
        select(User).where(User.username == login_data.username)
    )
    user = result.scalar_one_or_none()

    # Check if RADIUS is enabled
    radius_result = await db.execute(select(Setting).where(Setting.key == "radius_activate"))
    radius_setting = radius_result.scalar_one_or_none()
    radius_enabled = radius_setting and radius_setting.value and radius_setting.value.lower() == "true"

    authenticated = False
    if radius_enabled:
        authenticated = await _radius_authenticate(login_data.username, login_data.password, db)

    if not authenticated:
        # Fall back to local auth
        if user and verify_password(login_data.password, user.password_hash):
            authenticated = True

    if not authenticated or not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not user.enabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
        )

    # Create session
    session_id = generate_session_id()
    expires_at = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    session = Session(
        id=session_id,
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        expires_at=expires_at,
    )
    db.add(session)

    # Update user last login
    user.last_login = datetime.utcnow()
    user.last_activity = datetime.utcnow()
    user.ip_address = request.client.host if request.client else None

    await db.commit()

    # Set session cookie (secure=False in debug mode for HTTP development)
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=not settings.debug,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
    )

    # Check for login banner
    login_banner = None
    require_terms = False
    terms_result = await db.execute(select(Setting).where(Setting.key == "login_terms"))
    terms_setting = terms_result.scalar_one_or_none()
    if terms_setting and terms_setting.value:
        login_banner = terms_setting.value

    req_terms_result = await db.execute(select(Setting).where(Setting.key == "require_terms_acceptance"))
    req_terms_setting = req_terms_result.scalar_one_or_none()
    if req_terms_setting and req_terms_setting.value and req_terms_setting.value.lower() == "true":
        require_terms = True

    return LoginResponse(
        session_id=session_id,
        username=user.username,
        privilege_level=user.privilege_level,
        privilege_name=PRIVILEGE_LEVELS.get(user.privilege_level, "Unknown"),
        expires_at=expires_at,
        login_banner=login_banner,
        require_terms_acceptance=require_terms,
    )


@router.post("/logout")
async def logout(
    response: Response,
    session: Session = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
):
    """Logout and invalidate session."""
    await db.delete(session)
    await db.commit()

    # Clear session cookie
    response.delete_cookie("session_id")

    return {"message": "Logged out successfully"}


@router.get("/session", response_model=SessionInfo)
async def get_session(
    session: Session = Depends(get_current_session),
    user: User = Depends(get_current_user),
):
    """Get current session information."""
    return SessionInfo(
        session_id=session.id,
        user_id=user.id,
        username=user.username,
        privilege_level=user.privilege_level,
        privilege_name=PRIVILEGE_LEVELS.get(user.privilege_level, "Unknown"),
        ip_address=session.ip_address,
        created_at=session.created_at,
        last_activity=session.last_activity,
        expires_at=session.expires_at,
    )


@router.post("/refresh")
async def refresh_session(
    response: Response,
    session: Session = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
):
    """Refresh session expiration."""
    session.expires_at = datetime.utcnow() + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    await db.commit()

    # Update cookie (secure=False in debug mode for HTTP development)
    response.set_cookie(
        key="session_id",
        value=session.id,
        httponly=True,
        secure=not settings.debug,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
    )

    return {"message": "Session refreshed", "expires_at": session.expires_at}
