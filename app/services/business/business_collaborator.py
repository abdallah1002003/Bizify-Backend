"""
Business Collaborator CRUD operations.
"""
from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import BusinessCollaborator
from app.models.enums import CollaboratorRole

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
# BusinessCollaborator
# ----------------------------

def get_collaborator(db: Session, id: UUID) -> Optional[BusinessCollaborator]:
    return db.query(BusinessCollaborator).filter(BusinessCollaborator.id == id).first()


def get_business_collaborator(db: Session, id: UUID) -> Optional[BusinessCollaborator]:
    return get_collaborator(db, id=id)


def get_collaborators(db: Session, business_id: UUID) -> List[BusinessCollaborator]:
    return db.query(BusinessCollaborator).filter(BusinessCollaborator.business_id == business_id).all()


def get_business_collaborators(db: Session, skip: int = 0, limit: int = 100) -> List[BusinessCollaborator]:
    return db.query(BusinessCollaborator).offset(skip).limit(limit).all()


def add_collaborator(
    db: Session,
    business_id: UUID,
    user_id: UUID,
    role: CollaboratorRole,
) -> BusinessCollaborator:
    existing = (
        db.query(BusinessCollaborator)
        .filter(
            BusinessCollaborator.business_id == business_id,
            BusinessCollaborator.user_id == user_id,
        )
        .first()
    )
    if existing is not None:
        existing.role = role
        db.commit()
        db.refresh(existing)
        return existing

    db_obj = BusinessCollaborator(business_id=business_id, user_id=user_id, role=role)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def create_business_collaborator(db: Session, obj_in: Any) -> BusinessCollaborator:
    data = _to_update_dict(obj_in)
    return add_collaborator(
        db,
        business_id=data["business_id"],
        user_id=data["user_id"],
        role=data["role"],
    )


def update_business_collaborator(db: Session, db_obj: BusinessCollaborator, obj_in: Any) -> BusinessCollaborator:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def remove_collaborator(db: Session, business_id: UUID, user_id: UUID) -> None:
    db_obj = (
        db.query(BusinessCollaborator)
        .filter(
            BusinessCollaborator.business_id == business_id,
            BusinessCollaborator.user_id == user_id,
        )
        .first()
    )
    if db_obj is None:
        return

    if db_obj.role == CollaboratorRole.OWNER:
        raise PermissionError("Cannot remove owner collaborator")

    db.delete(db_obj)
    db.commit()


def delete_business_collaborator(db: Session, id: UUID) -> Optional[BusinessCollaborator]:
    db_obj = get_business_collaborator(db, id=id)
    if not db_obj:
        return None

    if db_obj.role == CollaboratorRole.OWNER:
        raise PermissionError("Cannot remove owner collaborator")

    db.delete(db_obj)
    db.commit()
    return db_obj
