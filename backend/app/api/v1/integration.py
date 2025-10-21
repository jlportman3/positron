"""Integration API endpoints"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db

router = APIRouter()


@router.get("/systems")
async def list_integration_systems(db: AsyncSession = Depends(get_db)):
    """List configured integration systems"""
    return {
        "systems": []
    }


@router.post("/sync/{system_type}")
async def trigger_sync(
    system_type: str,
    db: AsyncSession = Depends(get_db)
):
    """Trigger manual sync with billing system"""
    return {
        "status": "sync_initiated",
        "system_type": system_type
    }
