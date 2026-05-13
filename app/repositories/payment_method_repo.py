import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.models.payment_method import PaymentMethod
from app.repositories.base import BaseRepository
from app.schemas.payment_method import PaymentMethodCreate


class CRUDPaymentMethod(BaseRepository[PaymentMethod, PaymentMethodCreate, PaymentMethodCreate]):
    def get_by_user(self, db: Session, user_id: uuid.UUID) -> list[PaymentMethod]:
        return db.query(PaymentMethod).filter(PaymentMethod.user_id == user_id).all()

    def get_default_by_user(self, db: Session, user_id: uuid.UUID) -> Optional[PaymentMethod]:
        return (
            db.query(PaymentMethod)
            .filter(PaymentMethod.user_id == user_id, PaymentMethod.is_default.is_(True))
            .first()
        )

    def set_default(self, db: Session, method_id: uuid.UUID, user_id: uuid.UUID) -> Optional[PaymentMethod]:
        # Reset current defaults
        db.query(PaymentMethod).filter(
            PaymentMethod.user_id == user_id, PaymentMethod.is_default.is_(True)
        ).update({"is_default": False})

        # Set new default
        method = db.query(PaymentMethod).filter(PaymentMethod.id == method_id, PaymentMethod.user_id == user_id).first()
        if method:
            method.is_default = True
            db.commit()
            db.refresh(method)
        return method

payment_method_repo = CRUDPaymentMethod(PaymentMethod)
