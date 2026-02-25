"""
Payment Method CRUD operations.
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import PaymentMethod
from app.services.billing.crud_utils import get_by_id, list_records
from app.core.crud_utils import _to_update_dict, _apply_updates  # type: ignore

logger = logging.getLogger(__name__)


# ----------------------------
# PaymentMethod
# ----------------------------

def get_payment_method(db: Session, id: UUID) -> Optional[PaymentMethod]:
    """Return a single payment method by id."""

    return get_by_id(db, PaymentMethod, id)


def get_payment_methods(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
) -> List[PaymentMethod]:
    """Return paginated payment methods, optionally filtered by user."""

    return list_records(
        db,
        PaymentMethod,
        skip=skip,
        limit=limit,
        filters={"user_id": user_id},
    )


def create_payment_method(db: Session, obj_in: Any) -> PaymentMethod:
    """Create a payment method record."""

    db_obj = PaymentMethod(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_payment_method(db: Session, db_obj: PaymentMethod, obj_in: Any) -> PaymentMethod:
    """Update mutable fields on an existing payment method."""

    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_payment_method(db: Session, id: UUID) -> Optional[PaymentMethod]:
    """Delete a payment method by id."""

    db_obj = get_payment_method(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj
