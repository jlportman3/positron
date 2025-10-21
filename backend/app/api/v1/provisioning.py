"""Provisioning API endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

from ...database import get_db
from ...services.provisioning import ProvisioningEngine

router = APIRouter()


# Pydantic schemas
class ProvisionRequest(BaseModel):
    subscriber_id: UUID
    gam_port_id: UUID
    bandwidth_plan_id: UUID
    vlan_id: Optional[int] = None


class BandwidthUpdateRequest(BaseModel):
    bandwidth_plan_id: UUID


@router.post("/provision")
async def provision_subscriber(
    request: ProvisionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Provision subscriber service"""
    engine = ProvisioningEngine(db)

    # Validate first
    validation = await engine.validate_provisioning(
        request.gam_port_id,
        request.bandwidth_plan_id
    )

    if not validation['valid']:
        raise HTTPException(status_code=400, detail=validation['errors'])

    # Provision
    result = await engine.provision_subscriber(
        request.subscriber_id,
        request.gam_port_id,
        request.bandwidth_plan_id,
        request.vlan_id
    )

    if not result['success']:
        raise HTTPException(status_code=500, detail=result.get('error'))

    return result


@router.post("/deprovision/{subscriber_id}")
async def deprovision_subscriber(
    subscriber_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Deprovision subscriber service"""
    engine = ProvisioningEngine(db)
    result = await engine.deprovision_subscriber(subscriber_id)

    if not result['success']:
        raise HTTPException(status_code=500, detail=result.get('error'))

    return result


@router.post("/update-bandwidth/{subscriber_id}")
async def update_subscriber_bandwidth(
    subscriber_id: UUID,
    request: BandwidthUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update subscriber bandwidth plan"""
    engine = ProvisioningEngine(db)
    result = await engine.update_subscriber_bandwidth(
        subscriber_id,
        request.bandwidth_plan_id
    )

    if not result['success']:
        raise HTTPException(status_code=500, detail=result.get('error'))

    return result


@router.post("/validate")
async def validate_provisioning(
    gam_port_id: UUID,
    bandwidth_plan_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Validate provisioning request"""
    engine = ProvisioningEngine(db)
    result = await engine.validate_provisioning(gam_port_id, bandwidth_plan_id)
    return result
