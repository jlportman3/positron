"""Subscriber API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr

from ...database import get_db
from ...models.subscriber import Subscriber, SubscriberStatus

router = APIRouter()


# Pydantic schemas
class SubscriberCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    service_address: str
    endpoint_mac: Optional[str] = None
    external_id: Optional[str] = None


class SubscriberUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    service_address: Optional[str] = None
    status: Optional[SubscriberStatus] = None


class SubscriberResponse(BaseModel):
    id: UUID
    name: str
    email: str
    phone: Optional[str]
    service_address: str
    status: SubscriberStatus
    endpoint_mac: Optional[str]
    vlan_id: Optional[int]
    external_id: Optional[str]

    class Config:
        from_attributes = True


@router.post("/", response_model=SubscriberResponse, status_code=status.HTTP_201_CREATED)
async def create_subscriber(
    subscriber: SubscriberCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create new subscriber"""
    new_subscriber = Subscriber(
        name=subscriber.name,
        email=subscriber.email,
        phone=subscriber.phone,
        service_address=subscriber.service_address,
        endpoint_mac=subscriber.endpoint_mac,
        external_id=subscriber.external_id,
        status=SubscriberStatus.PENDING
    )

    db.add(new_subscriber)
    await db.commit()
    await db.refresh(new_subscriber)
    return new_subscriber


@router.get("/", response_model=List[SubscriberResponse])
async def list_subscribers(
    status: Optional[SubscriberStatus] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List all subscribers"""
    query = select(Subscriber)

    if status:
        query = query.where(Subscriber.status == status)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    subscribers = list(result.scalars().all())
    return subscribers


@router.get("/{subscriber_id}", response_model=SubscriberResponse)
async def get_subscriber(
    subscriber_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get specific subscriber"""
    result = await db.execute(
        select(Subscriber).where(Subscriber.id == subscriber_id)
    )
    subscriber = result.scalar_one_or_none()

    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")

    return subscriber


@router.put("/{subscriber_id}", response_model=SubscriberResponse)
async def update_subscriber(
    subscriber_id: UUID,
    updates: SubscriberUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update subscriber"""
    result = await db.execute(
        select(Subscriber).where(Subscriber.id == subscriber_id)
    )
    subscriber = result.scalar_one_or_none()

    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")

    for key, value in updates.model_dump(exclude_unset=True).items():
        setattr(subscriber, key, value)

    await db.commit()
    await db.refresh(subscriber)
    return subscriber


@router.delete("/{subscriber_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscriber(
    subscriber_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete subscriber"""
    result = await db.execute(
        select(Subscriber).where(Subscriber.id == subscriber_id)
    )
    subscriber = result.scalar_one_or_none()

    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")

    await db.delete(subscriber)
    await db.commit()
