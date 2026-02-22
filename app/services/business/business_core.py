"""
Core Business CRUD operations.
"""
from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Business, BusinessCollaborator
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
# Business CRUD
# ----------------------------

def get_business(db: Session, id: UUID) -> Optional[Business]:
    return db.query(Business).filter(Business.id == id).first()


def get_businesses(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    owner_id: Optional[UUID] = None,
) -> List[Business]:
    """Retrieve businesses with optional owner filtering.
    
    Args:
        db: Database session
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        owner_id: Optional UUID to filter by business owner
        
    Returns:
        List of Business records, filtered by owner if provided
    """
    query = db.query(Business)
    if owner_id is not None:
        query = query.filter(Business.owner_id == owner_id)
    return query.offset(skip).limit(limit).all()


def create_business(db: Session, obj_in: Any) -> Business:
    """Create a new business with auto-initialization.
    
    Automatically creates an associated roadmap and adds the owner as a collaborator.
    
    Args:
        db: Database session
        obj_in: Business data (must include owner_id)
        
    Returns:
        Created Business instance with initialized roadmap and owner collaboration
        
    Raises:
        SQLAlchemyError: If database operations fail
    """
    from app.services.business import business_roadmap
    
    db_obj = Business(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)

    # Ensure roadmap exists.
    if not business_roadmap.get_roadmap(db, business_id=db_obj.id):
        business_roadmap.init_default_roadmap(db, db_obj.id)

    # Ensure owner collaborator exists.
    from app.services.business import business_collaborator
    owner_collab = (
        db.query(BusinessCollaborator)
        .filter(
            BusinessCollaborator.business_id == db_obj.id,
            BusinessCollaborator.user_id == db_obj.owner_id,
        )
        .first()
    )
    if owner_collab is None:
        business_collaborator.add_collaborator(db, db_obj.id, db_obj.owner_id, CollaboratorRole.OWNER)

    return db_obj


def update_business(db: Session, db_obj: Business, obj_in: Any) -> Business:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_business(db: Session, id: UUID) -> Optional[Business]:
    db_obj = get_business(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


def update_business_stage(db: Session, business_id: UUID, new_stage) -> Optional[Business]:
    db_obj = get_business(db, business_id)
    if db_obj is None:
        return None
    db_obj.stage = new_stage
    db.commit()
    db.refresh(db_obj)
    return db_obj
