# ruff: noqa
"""
Admin Action Log CRUD operations.
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import AdminActionLog

logger = logging.getLogger(__name__)

from app.core.crud_utils import _to_update_dict, _apply_updates

# ----------------------------
# AdminActionLog CRUD
# ----------------------------

def get_admin_action_log(db: Session, id: UUID) -> Optional[AdminActionLog]:
    return db.query(AdminActionLog).filter(AdminActionLog.id == id).first()


def get_admin_action_logs(db: Session, skip: int = 0, limit: int = 100) -> List[AdminActionLog]:
    return (
        db.query(AdminActionLog)
        .order_by(AdminActionLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_admin_action_log(db: Session, obj_in: Any) -> AdminActionLog:
    data = _to_update_dict(obj_in)
    db_obj = AdminActionLog(**data)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_admin_action_log(db: Session, db_obj: AdminActionLog, obj_in: Any) -> AdminActionLog:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_admin_action_log(db: Session, id: UUID) -> Optional[AdminActionLog]:
    db_obj = get_admin_action_log(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


# Backward-compatible alias used by older code.
def get_admin_logs(db: Session, skip: int = 0, limit: int = 100) -> List[AdminActionLog]:
    return get_admin_action_logs(db, skip=skip, limit=limit)
