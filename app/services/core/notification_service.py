"""
Notification CRUD operations.
"""
from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Notification

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
# Notification CRUD
# ----------------------------

def get_notification(db: Session, id: UUID) -> Optional[Notification]:
    return db.query(Notification).filter(Notification.id == id).first()


def get_notifications(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
) -> List[Notification]:
    query = db.query(Notification)
    if user_id is not None:
        query = query.filter(Notification.user_id == user_id)
    return query.offset(skip).limit(limit).all()


def create_notification(db: Session, obj_in: Any) -> Notification:
    db_obj = Notification(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_notification(db: Session, db_obj: Notification, obj_in: Any) -> Notification:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_notification(db: Session, id: UUID) -> Optional[Notification]:
    db_obj = get_notification(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


# Backward compatibility alias
emit_notification = create_notification
