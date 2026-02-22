"""
Billing Plan CRUD operations.
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Plan
from app.services.billing.crud_utils import get_by_id, list_records
from app.services.billing.billing_service import _to_update_dict, _apply_updates

logger = logging.getLogger(__name__)


# ----------------------------
# Plan
# ----------------------------

def get_plan(db: Session, id: UUID) -> Optional[Plan]:
    """Return a single plan by id."""

    return get_by_id(db, Plan, id)


def get_plans(db: Session, skip: int = 0, limit: int = 100) -> List[Plan]:
    """Return paginated plan records."""

    return list_records(db, Plan, skip=skip, limit=limit)


def create_plan(db: Session, obj_in: Any) -> Plan:
    """Create a new billing plan."""

    db_obj = Plan(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_plan(db: Session, db_obj: Plan, obj_in: Any) -> Plan:
    """Update mutable fields on an existing plan."""

    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_plan(db: Session, id: UUID) -> Optional[Plan]:
    """Delete a plan by id and return the deleted record."""

    db_obj = get_plan(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj
