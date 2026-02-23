"""
Idea Access CRUD operations.
"""
from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import IdeaAccess

logger = logging.getLogger(__name__)

from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates

# ----------------------------
# IdeaAccess CRUD
# ----------------------------

def get_idea_access(db: Session, id: UUID) -> Optional[IdeaAccess]:
    return db.query(IdeaAccess).filter(IdeaAccess.id == id).first()


def get_idea_accesses(db: Session, skip: int = 0, limit: int = 100) -> List[IdeaAccess]:
    return db.query(IdeaAccess).offset(skip).limit(limit).all()


def get_idea_accesses_by_owner(db: Session, owner_id: UUID, skip: int = 0, limit: int = 100) -> List[IdeaAccess]:
    from app.models.ideation.idea import Idea
    return (
        db.query(IdeaAccess)
        .join(Idea, IdeaAccess.idea_id == Idea.id)
        .filter(Idea.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_idea_access(db: Session, obj_in: Any) -> IdeaAccess:
    db_obj = IdeaAccess(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_idea_access(db: Session, db_obj: IdeaAccess, obj_in: Any) -> IdeaAccess:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_idea_access(db: Session, id: UUID) -> Optional[IdeaAccess]:
    db_obj = get_idea_access(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj
