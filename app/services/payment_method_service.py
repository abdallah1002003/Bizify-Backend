import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.payment_method import PaymentMethod
from app.repositories.payment_method_repo import payment_method_repo
from app.schemas.payment_method import PaymentMethodCreate


def get_user_payment_methods(db: Session, user_id: uuid.UUID) -> list[PaymentMethod]:
    return payment_method_repo.get_by_user(db, user_id=user_id)


def add_payment_method(db: Session, user_id: uuid.UUID, obj_in: PaymentMethodCreate) -> PaymentMethod:
    obj_in.user_id = user_id
    
    # If it's the first one, make it default
    existing = payment_method_repo.get_by_user(db, user_id=user_id)
    if not existing:
        obj_in.is_default = True

    return payment_method_repo.create(db, obj_in=obj_in)


def set_default_payment_method(db: Session, user_id: uuid.UUID, method_id: uuid.UUID) -> PaymentMethod:
    method = payment_method_repo.set_default(db, method_id=method_id, user_id=user_id)
    if not method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment method not found."
        )
    return method


def delete_payment_method(db: Session, user_id: uuid.UUID, method_id: uuid.UUID) -> None:
    method = payment_method_repo.get(db, id=method_id)
    if not method or method.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment method not found."
        )
    payment_method_repo.remove(db, id=method_id)
