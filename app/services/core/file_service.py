# ruff: noqa
# type: ignore
"""
File CRUD operations.
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import File

logger = logging.getLogger(__name__)

from app.core.crud_utils import _to_update_dict, _apply_updates

# ----------------------------
# File CRUD
# ----------------------------

def get_file(db: Session, id: UUID) -> Optional[File]:
    return db.query(File).filter(File.id == id).first()


def get_files(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    owner_id: Optional[UUID] = None,
) -> List[File]:
    query = db.query(File)
    if owner_id is not None:
        query = query.filter(File.owner_id == owner_id)
    return query.offset(skip).limit(limit).all()


def create_file(db: Session, obj_in: Any) -> File:
    db_obj = File(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_file(db: Session, db_obj: File, obj_in: Any) -> File:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_file(db: Session, id: UUID) -> Optional[File]:
    db_obj = get_file(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


# Backward compatibility alias
create_file_record = create_file
