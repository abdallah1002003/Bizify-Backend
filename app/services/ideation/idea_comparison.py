"""
Idea Comparison CRUD operations.
"""
from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import IdeaComparison

logger = logging.getLogger(__name__)

from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates

# ----------------------------
# IdeaComparison CRUD
# ----------------------------

def get_idea_comparison(db: Session, id: UUID) -> Optional[IdeaComparison]:
    return db.query(IdeaComparison).filter(IdeaComparison.id == id).first()


def get_idea_comparisons(db: Session, skip: int = 0, limit: int = 100) -> List[IdeaComparison]:
    return db.query(IdeaComparison).offset(skip).limit(limit).all()


def create_idea_comparison(db: Session, obj_in: Any) -> IdeaComparison:
    db_obj = IdeaComparison(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_idea_comparison(db: Session, db_obj: IdeaComparison, obj_in: Any) -> IdeaComparison:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_idea_comparison(db: Session, id: UUID) -> Optional[IdeaComparison]:
    db_obj = get_idea_comparison(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


def create_comparison(db: Session, title: str, user_id: UUID) -> IdeaComparison:
    return create_idea_comparison(db, {"name": title, "user_id": user_id})
