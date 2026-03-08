from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from sqlalchemy.ext.asyncio import AsyncSession
import app.models as models
from app.core.dependencies import get_current_active_user
from app.db.database import get_async_db
from app.schemas.billing.subscription import SubscriptionCreate, SubscriptionUpdate, SubscriptionResponse
from app.services.billing import subscription_service as service

router = APIRouter()


def _ensure_subscription_owner(subscription: models.Subscription, current_user: models.User) -> None:
    if subscription.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")


@router.get("/", response_model=List[SubscriptionResponse])
async def read_subscriptions(
    skip: SkipParam = 0,
    limit: LimitParam = 20,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """List subscriptions for current user with pagination.
    
    Query Parameters:
        skip: Number of records to skip (default: 0)
        limit: Number of records to return (default: 20, max: 100)
        
    Returns:
        List of Subscription records for the authenticated user
    """
    return await service.get_subscriptions(db, skip=skip, limit=limit, user_id=current_user.id)

@router.post("/", response_model=SubscriptionResponse)
async def create_subscription(
    item_in: SubscriptionCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    data = item_in.model_dump()
    data["user_id"] = current_user.id
    return await service.create_subscription(db, obj_in=data)

@router.get("/{id}", response_model=SubscriptionResponse)
async def read_subscription(
    id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_subscription(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Subscription not found")
    _ensure_subscription_owner(db_obj, current_user)
    return db_obj

@router.put("/{id}", response_model=SubscriptionResponse)
async def update_subscription(
    id: UUID,
    item_in: SubscriptionUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_subscription(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Subscription not found")
    _ensure_subscription_owner(db_obj, current_user)
    data = item_in.model_dump(exclude_unset=True)
    data.pop("user_id", None)
    return await service.update_subscription(db, db_obj=db_obj, obj_in=data)

@router.delete("/{id}", response_model=SubscriptionResponse)
async def delete_subscription(
    id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = await service.get_subscription(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Subscription not found")
    _ensure_subscription_owner(db_obj, current_user)
    return await service.delete_subscription(db, id=id)
