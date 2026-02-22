"""
Billing Plan CRUD operations.
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Plan
from app.services.billing.billing_service import _to_update_dict, _apply_updates

logger = logging.getLogger(__name__)


# ----------------------------
# Plan
# ----------------------------

def get_plan(db: Session, id: UUID) -> Optional[Plan]:
    return db.query(Plan).filter(Plan.id == id).first()


def get_plans(db: Session, skip: int = 0, limit: int = 100) -> List[Plan]:
    return db.query(Plan).offset(skip).limit(limit).all()


def create_plan(db: Session, obj_in: Any) -> Plan:
    db_obj = Plan(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_plan(db: Session, db_obj: Plan, obj_in: Any) -> Plan:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_plan(db: Session, id: UUID) -> Optional[Plan]:
    db_obj = get_plan(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj
