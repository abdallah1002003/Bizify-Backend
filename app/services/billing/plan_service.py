"""
Billing Plan CRUD operations.
"""
from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Plan

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
