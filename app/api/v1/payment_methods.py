import uuid
from typing import Any, List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.payment_method import PaymentMethodCreate, PaymentMethodRead
from app.services import payment_method_service

router = APIRouter()


@router.get("/", response_model=List[PaymentMethodRead])
def list_payment_methods(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Return all saved payment methods for the authenticated user."""
    return payment_method_service.get_user_payment_methods(db, user_id=current_user.id)


@router.post("/", response_model=PaymentMethodRead, status_code=status.HTTP_201_CREATED)
def add_payment_method(
    body: PaymentMethodCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Add a new payment method for the user."""
    return payment_method_service.add_payment_method(db, user_id=current_user.id, obj_in=body)


@router.put("/{method_id}/default", response_model=PaymentMethodRead)
def set_default_payment_method(
    method_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Set a specific payment method as default."""
    return payment_method_service.set_default_payment_method(db, user_id=current_user.id, method_id=method_id)


@router.delete("/{method_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment_method(
    method_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete a saved payment method."""
    payment_method_service.delete_payment_method(db, user_id=current_user.id, method_id=method_id)
