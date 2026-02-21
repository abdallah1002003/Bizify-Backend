from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import app.models as models
from app.core.dependencies import get_current_active_user
from app.db.database import get_db
from app.schemas.billing.payment_method import PaymentMethodCreate, PaymentMethodUpdate, PaymentMethodResponse
from app.services.billing import billing_service as service

router = APIRouter()


def _ensure_payment_method_owner(payment_method: models.PaymentMethod, current_user: models.User) -> None:
    if payment_method.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")


@router.get("/", response_model=List[PaymentMethodResponse])
def read_payment_methods(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    return service.get_payment_methods(db, skip=skip, limit=limit, user_id=current_user.id)

@router.post("/", response_model=PaymentMethodResponse)
def create_payment_method(
    item_in: PaymentMethodCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    data = item_in.model_dump()
    data["user_id"] = current_user.id
    return service.create_payment_method(db, obj_in=data)

@router.get("/{id}", response_model=PaymentMethodResponse)
def read_payment_method(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = service.get_payment_method(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="PaymentMethod not found")
    _ensure_payment_method_owner(db_obj, current_user)
    return db_obj

@router.put("/{id}", response_model=PaymentMethodResponse)
def update_payment_method(
    id: UUID,
    item_in: PaymentMethodUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = service.get_payment_method(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="PaymentMethod not found")
    _ensure_payment_method_owner(db_obj, current_user)
    data = item_in.model_dump(exclude_unset=True)
    data.pop("user_id", None)
    return service.update_payment_method(db, db_obj=db_obj, obj_in=data)

@router.delete("/{id}", response_model=PaymentMethodResponse)
def delete_payment_method(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_obj = service.get_payment_method(db, id=id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="PaymentMethod not found")
    _ensure_payment_method_owner(db_obj, current_user)
    return service.delete_payment_method(db, id=id)
