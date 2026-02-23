"""
Idea Version CRUD operations.
"""
from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import IdeaVersion

logger = logging.getLogger(__name__)

from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates

# ----------------------------
# IdeaVersion CRUD
# ----------------------------

def get_idea_version(db: Session, id: UUID) -> Optional[IdeaVersion]:
    return db.query(IdeaVersion).filter(IdeaVersion.id == id).first()


def get_idea_versions(
    db: Session,
    idea_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[IdeaVersion]:
    query = db.query(IdeaVersion)
    if idea_id is not None:
        query = query.filter(IdeaVersion.idea_id == idea_id)
    return query.order_by(IdeaVersion.created_at.desc()).offset(skip).limit(limit).all()


def create_idea_version(db: Session, obj_in: Any) -> IdeaVersion:
    db_obj = IdeaVersion(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_idea_version(db: Session, db_obj: IdeaVersion, obj_in: Any) -> IdeaVersion:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_idea_version(db: Session, id: UUID) -> Optional[IdeaVersion]:
    db_obj = get_idea_version(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj
