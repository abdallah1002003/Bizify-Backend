from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Business, BusinessCollaborator
from app.models.enums import CollaboratorRole
from app.services.base_service import BaseService
from app.services.interfaces import IBusinessRoadmapService, IBusinessCollaboratorService
from app.services.business.business_roadmap import BusinessRoadmapService, get_business_roadmap_service
from app.services.business.business_collaborator import BusinessCollaboratorService, get_business_collaborator_service
from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates
from app.core.events import dispatcher

logger = logging.getLogger(__name__)


class BusinessService(BaseService):
    """Main service for managing Businesses, delegating to roadmap and collaborator services."""

    def __init__(
        self,
        db: Session,
        roadmap_service: IBusinessRoadmapService,
        collaborator_service: IBusinessCollaboratorService
    ):
        super().__init__(db)
        self.roadmap = roadmap_service
        self.collaborator = collaborator_service

    # ----------------------------
    # Business CRUD
    # ----------------------------

    def get_business(self, id: UUID) -> Optional[Business]:
        return self.db.query(Business).filter(Business.id == id).first()

    def get_businesses(
        self,
        skip: int = 0,
        limit: int = 100,
        owner_id: Optional[UUID] = None,
    ) -> List[Business]:
        """Retrieve businesses with optional owner filtering."""
        from sqlalchemy.orm import selectinload
        
        query = self.db.query(Business).options(
            selectinload(Business.owner),
            selectinload(Business.collaborators).selectinload(BusinessCollaborator.user),
            selectinload(Business.roadmap)
        )
        if owner_id is not None:
            query = query.filter(Business.owner_id == owner_id)
        return query.offset(skip).limit(limit).all()

    def create_business(self, obj_in: Any) -> Business:
        """Create a new business and emit creation event."""
        db_obj = Business(**_to_update_dict(obj_in))
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)

        # Restore synchronous side-effect: default roadmap
        self.roadmap.init_default_roadmap(db_obj.id)
        return db_obj

    def update_business(self, db_obj: Business, obj_in: Any) -> Business:
        _apply_updates(db_obj, _to_update_dict(obj_in))
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete_business(self, id: UUID) -> Optional[Business]:
        db_obj = self.get_business(id=id)
        if not db_obj:
            return None

        self.db.delete(db_obj)
        self.db.commit()
        return db_obj

    def update_business_stage(self, business_id: UUID, new_stage: Any) -> Optional[Business]:
        db_obj = self.get_business(business_id)
        if db_obj is None:
            return None
        db_obj.stage = new_stage
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj


def get_business_service(
    db: Session = Depends(get_db),
    roadmap: IBusinessRoadmapService = Depends(get_business_roadmap_service),
    collaborator: IBusinessCollaboratorService = Depends(get_business_collaborator_service),
) -> BusinessService:
    """Dependency provider for BusinessService."""
    return BusinessService(db, roadmap, collaborator)


# Legacy aliases (Supports older tests calling functions directly)
def get_business_service_manual(db: Session) -> BusinessService:
    from app.services.business.business_roadmap import BusinessRoadmapService
    from app.services.business.business_collaborator import BusinessCollaboratorService
    return BusinessService(
        db=db,
        roadmap_service=BusinessRoadmapService(db),
        collaborator_service=BusinessCollaboratorService(db)
    )

def get_business(db: Session, id: UUID) -> Optional[Business]:
    return get_business_service_manual(db).get_business(id)

def create_business(db: Session, obj_in: Any) -> Business:
    return get_business_service_manual(db).create_business(obj_in)

def update_business(db: Session, db_obj: Business, obj_in: Any) -> Business:
    return get_business_service_manual(db).update_business(db_obj, obj_in)

def delete_business(db: Session, id: UUID) -> Optional[Business]:
    return get_business_service_manual(db).delete_business(id)
