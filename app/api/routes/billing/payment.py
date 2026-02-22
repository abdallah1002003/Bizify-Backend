from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.pagination import LimitParam, SkipParam
from sqlalchemy.orm import Session
import app.models as models
from app.core.dependencies import get_current_active_user
from app.db.database import get_db
from app.schemas.billing.payment import PaymentCreate, PaymentUpdate, PaymentResponse
from app.services.billing import payment_method as payment_method_service
from app.services.billing import payment_service as service
from app.services.billing import subscription_service

router = APIRouter()


def _ensure_payment_owner(payment: models.Payment, current_user: models.User) -> None:
    if payment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")


@router.get("/", response_model=List[PaymentResponse])
def read_payments(
    skip: SkipParam = 0,
    limit: LimitParam = 20,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """List payments for current user with pagination.
    
    Query Parameters:
        skip: Number of records to skip (default: 0)
        limit: Number of records to return (default: 20, max: 100)
        
    Returns:
        List of Payment records for the authenticated user
    """
    return service.get_payments(db, skip=skip, limit=limit, user_id=current_user.id)

@router.post("/", response_model=PaymentResponse)
def create_payment(
    item_in: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    subscription = subscription_service.get_subscription(db, id=item_in.subscription_id)
    if subscription is None:
        raise HTTPException(status_code=404, detail="Subscription not found")
    if subscription.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    payment_method = payment_method_service.get_payment_method(db, id=item_in.payment_method_id)
    if payment_method is None:
        raise HTTPException(status_code=404, detail="Payment method not found")
    if payment_method.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    data = item_in.model_dump()
    data["user_id"] = current_user.id
    return service.create_payment(db, obj_in=data)

@router.get("/{id}", response_model=PaymentResponse)
def read_payment(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = service.get_payment(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Payment not found")
    _ensure_payment_owner(db_obj, current_user)
    return db_obj

@router.put("/{id}", response_model=PaymentResponse)
def update_payment(
    id: UUID,
    item_in: PaymentUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = service.get_payment(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Payment not found")
    _ensure_payment_owner(db_obj, current_user)

    data = item_in.model_dump(exclude_unset=True)
    data.pop("user_id", None)

    if "subscription_id" in data and data["subscription_id"] is not None:
        subscription = subscription_service.get_subscription(db, id=data["subscription_id"])
        if subscription is None:
            raise HTTPException(status_code=404, detail="Subscription not found")
        if subscription.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

    if "payment_method_id" in data and data["payment_method_id"] is not None:
        payment_method = payment_method_service.get_payment_method(
            db,
            id=data["payment_method_id"],
        )
        if payment_method is None:
            raise HTTPException(status_code=404, detail="Payment method not found")
        if payment_method.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

    return service.update_payment(db, db_obj=db_obj, obj_in=data)

@router.delete("/{id}", response_model=PaymentResponse)
def delete_payment(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = service.get_payment(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Payment not found")
    _ensure_payment_owner(db_obj, current_user)
    return service.delete_payment(db, id=id)
