"""
Core Idea CRUD operations and access control.
"""
from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Idea, IdeaAccess, IdeaVersion
logger = logging.getLogger(__name__)

from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates

def _create_snapshot(db: Session, idea: Idea, created_by: Optional[UUID] = None) -> IdeaVersion:
    """Create a snapshot/version of the idea."""
    snapshot = {
        "title": idea.title,
        "description": idea.description,
        "status": idea.status.value if hasattr(idea.status, "value") else str(idea.status),
        "ai_score": idea.ai_score,
        "is_archived": idea.is_archived,
    }
    db_obj = IdeaVersion(
        idea_id=idea.id,
        created_by=created_by or idea.owner_id,
        snapshot_json=snapshot,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


# ----------------------------
# Idea CRUD
# ----------------------------

def get_idea(db: Session, id: UUID, user_id: Optional[UUID] = None) -> Optional[Idea]:
    db_obj = db.query(Idea).filter(Idea.id == id).first()
    if db_obj is None:
        return None

    if user_id is not None and not check_idea_access(db, id, user_id, "view"):
        return None

    return db_obj


def get_ideas(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
) -> List[Idea]:
    query = db.query(Idea)
    if user_id is not None:
        query = query.outerjoin(IdeaAccess).filter(
            (Idea.owner_id == user_id) | (IdeaAccess.user_id == user_id)
        )
    return query.distinct().offset(skip).limit(limit).all()


def create_idea(db: Session, obj_in: Any) -> Idea:
    db_obj = Idea(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)

    _create_snapshot(db, db_obj)
    return db_obj


def update_idea(db: Session, db_obj: Idea, obj_in: Any, performer_id: Optional[UUID] = None) -> Idea:
    if performer_id is not None and not check_idea_access(db, db_obj.id, performer_id, "edit"):
        raise PermissionError("Not authorized to edit this idea")

    update_data = _to_update_dict(obj_in)
    major_changed = any(field in update_data for field in ("title", "description", "status"))

    _apply_updates(db_obj, update_data)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)

    if major_changed:
        _create_snapshot(db, db_obj, created_by=performer_id)

    return db_obj


def delete_idea(db: Session, id: UUID) -> Optional[Idea]:
    db_obj = db.query(Idea).filter(Idea.id == id).first()
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


# ----------------------------
# Access control
# ----------------------------

def check_idea_access(db: Session, idea_id: UUID, user_id: UUID, required_perm: str = "view") -> bool:
    idea = db.query(Idea).filter(Idea.id == idea_id).first()
    if idea is None:
        return False

    if idea.owner_id == user_id:
        return True

    access = (
        db.query(IdeaAccess)
        .filter(IdeaAccess.idea_id == idea_id, IdeaAccess.user_id == user_id)
        .first()
    )
    if access is None:
        return False

    if required_perm == "view":
        return True
    if required_perm == "edit":
        return bool(access.can_edit)
    if required_perm == "delete":
        return bool(access.can_delete)
    if required_perm == "experiment":
        return bool(access.can_experiment)

    return False


def grant_access(db: Session, idea_id: UUID, user_id: UUID, permissions: Dict[str, bool]) -> IdeaAccess:
    access = (
        db.query(IdeaAccess)
        .filter(IdeaAccess.idea_id == idea_id, IdeaAccess.user_id == user_id)
        .first()
    )
    if access is None:
        access = IdeaAccess(
            idea_id=idea_id,
            user_id=user_id,
            can_edit=permissions.get("edit", False),
            can_delete=permissions.get("delete", False),
            can_experiment=permissions.get("experiment", False),
        )
        db.add(access)
    else:
        access.can_edit = permissions.get("edit", access.can_edit)
        access.can_delete = permissions.get("delete", access.can_delete)
        access.can_experiment = permissions.get("experiment", access.can_experiment)

    db.commit()
    db.refresh(access)
    return access
