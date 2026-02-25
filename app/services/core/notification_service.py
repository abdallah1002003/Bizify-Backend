# ruff: noqa
"""
Notification CRUD operations.
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Notification

logger = logging.getLogger(__name__)

from app.core.crud_utils import _to_update_dict, _apply_updates

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
