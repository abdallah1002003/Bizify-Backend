"""
Usage enforcement and tracking operations.
"""
from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Usage

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
# Usage enforcement
# ----------------------------

def check_usage_limit(db: Session, user_id: UUID, resource_type: str) -> bool:
    usage = (
        db.query(Usage)
        .filter(Usage.user_id == user_id, Usage.resource_type == resource_type)
        .first()
    )
    if usage is None or usage.limit_value is None:
        return True
    return usage.used < usage.limit_value


def record_usage(db: Session, user_id: UUID, resource_type: str, quantity: int = 1) -> Usage:
    usage = (
        db.query(Usage)
        .filter(Usage.user_id == user_id, Usage.resource_type == resource_type)
        .first()
    )
    if usage is None:
        usage = Usage(user_id=user_id, resource_type=resource_type, used=0)
        db.add(usage)

    usage.used += quantity
    db.commit()
    db.refresh(usage)
    return usage


# ----------------------------
# Usage CRUD
# ----------------------------

def get_usage(db: Session, id: UUID) -> Optional[Usage]:
    return db.query(Usage).filter(Usage.id == id).first()


def get_usages(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
) -> List[Usage]:
    query = db.query(Usage)
    if user_id is not None:
        query = query.filter(Usage.user_id == user_id)
    return query.offset(skip).limit(limit).all()


def create_usage(db: Session, obj_in: Any) -> Usage:
    db_obj = Usage(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_usage(db: Session, db_obj: Usage, obj_in: Any) -> Usage:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_usage(db: Session, id: UUID) -> Optional[Usage]:
    db_obj = get_usage(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj
