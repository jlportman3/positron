"""Monitoring API endpoints"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from ...database import get_db

router = APIRouter()


@router.get("/health")
async def health_check():
    """System health check"""
    return {
        "status": "healthy",
        "service": "monitoring"
    }


@router.get("/devices/{device_id}/metrics")
async def get_device_metrics(
    device_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get device performance metrics"""
    # Placeholder for monitoring implementation
    return {
        "device_id": str(device_id),
        "metrics": {
            "cpu_usage": 0,
            "memory_usage": 0,
            "uptime": 0
        }
    }
