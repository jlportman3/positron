"""
Security utilities for authentication and authorization.
"""
import base64
import secrets
from datetime import datetime, timedelta
from typing import Optional
import bcrypt

from app.core.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def hash_password(password: str) -> str:
    """Hash a password."""
    return bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')


def generate_session_id() -> str:
    """Generate a secure random session ID."""
    return secrets.token_urlsafe(32)


def decode_basic_auth(auth_header: str) -> tuple[str, str]:
    """Decode Basic Authentication header.

    Args:
        auth_header: The Authorization header value (e.g., "Basic dXNlcjpwYXNz")

    Returns:
        Tuple of (username, password)

    Raises:
        ValueError: If the header is invalid
    """
    if not auth_header.startswith("Basic "):
        raise ValueError("Invalid authorization header")

    try:
        encoded = auth_header[6:]  # Remove "Basic " prefix
        decoded = base64.b64decode(encoded).decode("utf-8")
        username, password = decoded.split(":", 1)
        return username, password
    except Exception as e:
        raise ValueError(f"Invalid basic auth encoding: {e}")


def is_session_expired(last_activity: datetime, expires_at: datetime) -> bool:
    """Check if a session has expired.

    Args:
        last_activity: Last activity timestamp
        expires_at: Absolute expiration timestamp

    Returns:
        True if session is expired
    """
    now = datetime.utcnow()

    # Check absolute expiration
    if now > expires_at:
        return True

    # Check idle timeout
    idle_timeout = timedelta(minutes=settings.session_idle_timeout_minutes)
    if now - last_activity > idle_timeout:
        return True

    return False


# Privilege levels
PRIVILEGE_LEVELS = {
    0: "Device",  # Device accounts for announcements
    1: "Viewer",
    2: "Viewer+",
    3: "Operator",
    4: "Operator+",
    5: "Manager",
    6: "Manager+",
    7: "Admin",
    8: "Admin+",
    9: "SuperAdmin",
    10: "SuperAdmin+",
    11: "System",
    12: "System+",
    13: "Root",
    14: "Root+",
    15: "Master",
}


def has_permission(user_level: int, required_level: int) -> bool:
    """Check if user has required permission level.

    Args:
        user_level: User's privilege level
        required_level: Required level for the operation

    Returns:
        True if user has sufficient privileges
    """
    return user_level >= required_level
