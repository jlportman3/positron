"""
Database seeding script.

Creates initial admin user and default settings.
"""
import asyncio
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker, init_db
from app.core.security import hash_password
from app.core.config import settings
from app.models import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_users(db: AsyncSession):
    """Create default users."""
    # Check if admin exists
    result = await db.execute(
        select(User).where(User.username == "admin")
    )
    admin = result.scalar_one_or_none()

    if not admin:
        # Create admin user with admin/admin credentials
        admin = User(
            username="admin",
            email="admin@alamogam.local",
            password_hash=hash_password("admin"),
            enabled=True,
            is_device=False,
            privilege_level=15,  # Master level
            session_timeout=30,
            created_by="system",
        )
        db.add(admin)
        logger.info("Created admin user (admin/admin)")
    else:
        logger.info("Admin user already exists")

    # Create device user for announcements
    result = await db.execute(
        select(User).where(User.username == settings.device_username)
    )
    device_user = result.scalar_one_or_none()

    if not device_user:
        device_user = User(
            username=settings.device_username,
            email=f"{settings.device_username}@alamogam.local",
            password_hash=hash_password(settings.device_password),
            enabled=True,
            is_device=True,
            privilege_level=1,  # Device level
            session_timeout=30,
            created_by="system",
        )
        db.add(device_user)
        logger.info(f"Created device user ({settings.device_username})")
    else:
        logger.info("Device user already exists")

    await db.commit()


async def main():
    """Run database seeding."""
    logger.info("Initializing database...")
    await init_db()

    logger.info("Seeding database...")
    async with async_session_maker() as db:
        await seed_users(db)

    logger.info("Database seeding complete!")


if __name__ == "__main__":
    asyncio.run(main())
