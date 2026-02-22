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
