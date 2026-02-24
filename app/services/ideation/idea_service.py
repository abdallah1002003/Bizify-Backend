"""
Core Idea Service.
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Idea, IdeaAccess
from app.services.base_service import BaseService
from app.services.interfaces import IIdeaAccessService, IIdeaVersionService
from app.services.ideation.idea_access import IdeaAccessService, get_idea_access_service
from app.services.ideation.idea_version import IdeaVersionService, get_idea_version_service
from app.core.crud_utils import _to_update_dict, _apply_updates
from app.core.events import dispatcher

logger = logging.getLogger(__name__)


class IdeaService(BaseService):
    """Main service for managing Ideas, delegating to access and version services."""

    def __init__(
        self,
        db: Session,
        access_service: IIdeaAccessService,
        version_service: IIdeaVersionService
    ):
        super().__init__(db)
        self.access = access_service
        self.version = version_service

    # ----------------------------
    # Idea CRUD
    # ----------------------------

    def get_idea(self, id: UUID, user_id: Optional[UUID] = None) -> Optional[Idea]:
        """Retrieve an idea by ID with optional access control."""
        db_obj = self.db.query(Idea).filter(Idea.id == id).first()
        if db_obj is None:
            return None

        if user_id is not None and not self.access.check_idea_access(id, user_id, "view"):
            return None

        return db_obj

    def get_ideas(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[UUID] = None,
    ) -> List[Idea]:
        """Retrieve ideas with optional user-based filtering."""
        query = self.db.query(Idea)
        if user_id is not None:
            query = query.outerjoin(IdeaAccess).filter(
                (Idea.owner_id == user_id) | (IdeaAccess.user_id == user_id)
            )
        return query.distinct().offset(skip).limit(limit).all()

    def create_idea(self, obj_in: Any) -> Idea:
        """Create a new idea and its initial version snapshot."""
        db_obj = Idea(**_to_update_dict(obj_in))
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)

        # Restore synchronous side-effect: initial snapshot
        self.version.create_idea_snapshot(db_obj)
        return db_obj

    def update_idea(self, db_obj: Idea, obj_in: Any, performer_id: Optional[UUID] = None) -> Idea:
        """Update an idea and create a new version snapshot if major fields changed."""
        if performer_id is not None and not self.access.check_idea_access(db_obj.id, performer_id, "edit"):
            raise PermissionError("Not authorized to edit this idea")

        update_data = _to_update_dict(obj_in)
        major_changed = any(field in update_data for field in ("title", "description", "status"))

        _apply_updates(db_obj, update_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)

        # Restore synchronous side-effect: snapshot on major change
        if major_changed:
            self.version.create_idea_snapshot(db_obj, created_by=performer_id)

        return db_obj

    def delete_idea(self, id: UUID) -> Optional[Idea]:
        """Delete an idea from the system."""
        db_obj = self.db.query(Idea).filter(Idea.id == id).first()
        if not db_obj:
            return None

        self.db.delete(db_obj)
        self.db.commit()
        return db_obj

    def check_idea_access(self, idea_id: UUID, user_id: UUID, required_perm: str = "view") -> bool:
        """Helper to expose access check via this service."""
        return self.access.check_idea_access(idea_id, user_id, required_perm)


def get_idea_service(
    db: Session = Depends(get_db),
    access: IdeaAccessService = Depends(get_idea_access_service),
    version: IdeaVersionService = Depends(get_idea_version_service),
) -> IdeaService:
    """Dependency provider for IdeaService."""
    return IdeaService(db, access, version)


# Legacy aliases (Supports older tests calling functions directly)
def get_idea_service_manual(db: Session) -> IdeaService:
    from app.services.ideation.idea_access import IdeaAccessService
    from app.services.ideation.idea_version import IdeaVersionService
    return IdeaService(
        db=db,
        access_service=IdeaAccessService(db),
        version_service=IdeaVersionService(db)
    )

def get_idea(db: Session, id: UUID, user_id: Optional[UUID] = None) -> Optional[Idea]:
    return get_idea_service_manual(db).get_idea(id, user_id)

def create_idea(db: Session, obj_in: Any) -> Idea:
    return get_idea_service_manual(db).create_idea(obj_in)

def update_idea(db: Session, db_obj: Idea, obj_in: Any, performer_id: Optional[UUID] = None) -> Idea:
    return get_idea_service_manual(db).update_idea(db_obj, obj_in, performer_id)

def check_idea_access(db: Session, idea_id: UUID, user_id: UUID, required_perm: str = "view") -> bool:
    return get_idea_service_manual(db).check_idea_access(idea_id, user_id, required_perm)

def delete_idea(db: Session, id: UUID) -> Optional[Idea]:
    return get_idea_service_manual(db).delete_idea(id)
