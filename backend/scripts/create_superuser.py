#!/usr/bin/env python3
"""
Script to create a superuser in the database
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.utils.auth import get_password_hash
from app.config import settings
import uuid


async def create_superuser(username: str, email: str, password: str, full_name: str = None):
    """Create a superuser"""

    # Create async engine
    engine = create_async_engine(
        settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
        echo=True
    )

    # Create async session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        try:
            # Check if user already exists
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.username == username)
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                print(f"✗ User '{username}' already exists!")
                return False

            # Create new superuser
            hashed_password = get_password_hash(password)
            new_user = User(
                id=uuid.uuid4(),
                username=username,
                email=email,
                full_name=full_name,
                hashed_password=hashed_password,
                is_active=True,
                is_superuser=True
            )

            session.add(new_user)
            await session.commit()

            print(f"✓ Superuser created successfully!")
            print(f"  Username: {username}")
            print(f"  Email: {email}")
            print(f"  Is Superuser: True")
            print(f"  Is Active: True")
            return True

        except Exception as e:
            print(f"✗ Error creating superuser: {e}")
            await session.rollback()
            return False
        finally:
            await engine.dispose()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create a superuser")
    parser.add_argument("--username", required=True, help="Username")
    parser.add_argument("--email", required=True, help="Email address")
    parser.add_argument("--password", required=True, help="Password")
    parser.add_argument("--full-name", help="Full name (optional)")

    args = parser.parse_args()

    asyncio.run(create_superuser(
        username=args.username,
        email=args.email,
        password=args.password,
        full_name=args.full_name
    ))
