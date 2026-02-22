"""
Payment Method CRUD operations.
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import PaymentMethod
from app.services.billing.billing_service import _to_update_dict, _apply_updates

logger = logging.getLogger(__name__)


# ----------------------------
# PaymentMethod
# ----------------------------

def get_payment_method(db: Session, id: UUID) -> Optional[PaymentMethod]:
    return db.query(PaymentMethod).filter(PaymentMethod.id == id).first()


def get_payment_methods(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
) -> List[PaymentMethod]:
    query = db.query(PaymentMethod)
    if user_id is not None:
        query = query.filter(PaymentMethod.user_id == user_id)
    return query.offset(skip).limit(limit).all()


def create_payment_method(db: Session, obj_in: Any) -> PaymentMethod:
    db_obj = PaymentMethod(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_payment_method(db: Session, db_obj: PaymentMethod, obj_in: Any) -> PaymentMethod:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_payment_method(db: Session, id: UUID) -> Optional[PaymentMethod]:
    db_obj = get_payment_method(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj
