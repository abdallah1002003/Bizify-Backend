from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import app.models as models
from app.core.dependencies import get_current_active_user
from app.db.database import get_db
from app.schemas.billing.subscription import SubscriptionCreate, SubscriptionUpdate, SubscriptionResponse
from app.services.billing import billing_service as service

router = APIRouter()


def _ensure_subscription_owner(subscription: models.Subscription, current_user: models.User) -> None:
    if subscription.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")


@router.get("/", response_model=List[SubscriptionResponse])
def read_subscriptions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    return service.get_subscriptions(db, skip=skip, limit=limit, user_id=current_user.id)

@router.post("/", response_model=SubscriptionResponse)
def create_subscription(
    item_in: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    data = item_in.model_dump()
    data["user_id"] = current_user.id
    return service.create_subscription(db, obj_in=data)

@router.get("/{id}", response_model=SubscriptionResponse)
def read_subscription(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = service.get_subscription(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Subscription not found")
    _ensure_subscription_owner(db_obj, current_user)
    return db_obj

@router.put("/{id}", response_model=SubscriptionResponse)
def update_subscription(
    id: UUID,
    item_in: SubscriptionUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = service.get_subscription(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Subscription not found")
    _ensure_subscription_owner(db_obj, current_user)
    data = item_in.model_dump(exclude_unset=True)
    data.pop("user_id", None)
    return service.update_subscription(db, db_obj=db_obj, obj_in=data)

@router.delete("/{id}", response_model=SubscriptionResponse)
def delete_subscription(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = service.get_subscription(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Subscription not found")
    _ensure_subscription_owner(db_obj, current_user)
    return service.delete_subscription(db, id=id)
