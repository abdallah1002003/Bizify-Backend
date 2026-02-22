"""
Payment Method CRUD operations.
"""
from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import PaymentMethod

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_update_dict(obj_in: Any) -> Dict[str, Any]:
    if obj_in is None:
        return {}
    if hasattr(obj_in, "model_dump"):
        return obj_in.model_dump(exclude_unset=True)
    return dict(obj_in)


def _apply_updates(db_obj: Any, update_data: Dict[str, Any]) -> Any:
    for field, value in update_data.items():
        if hasattr(db_obj, field):
            setattr(db_obj, field, value)
    return db_obj


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
