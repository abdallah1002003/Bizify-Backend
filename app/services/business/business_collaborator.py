import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import BusinessCollaborator
from app.models.enums import CollaboratorRole
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict, _apply_updates
from app.core.events import dispatcher

logger = logging.getLogger(__name__)


class BusinessCollaboratorService(BaseService):
    """Service for managing Business Collaborators."""

    def get_collaborator(self, id: UUID) -> Optional[BusinessCollaborator]:
        return self.db.query(BusinessCollaborator).filter(BusinessCollaborator.id == id).first()  # type: ignore[no-any-return]

    def get_business_collaborator(self, id: UUID) -> Optional[BusinessCollaborator]:
        return self.get_collaborator(id=id)

    def get_collaborators(self, business_id: UUID) -> List[BusinessCollaborator]:
        return self.db.query(BusinessCollaborator).filter(BusinessCollaborator.business_id == business_id).all()  # type: ignore[no-any-return]

    def get_business_collaborators(self, skip: int = 0, limit: int = 100) -> List[BusinessCollaborator]:
        return self.db.query(BusinessCollaborator).offset(skip).limit(limit).all()  # type: ignore[no-any-return]

    def add_collaborator(
        self,
        business_id: UUID,
        user_id: UUID,
        role: CollaboratorRole,
    ) -> BusinessCollaborator:
        existing = (
            self.db.query(BusinessCollaborator)
            .filter(
                BusinessCollaborator.business_id == business_id,
                BusinessCollaborator.user_id == user_id,
            )
            .first()
        )
        if existing is not None:
            existing.role = role
            self.db.commit()
            self.db.refresh(existing)
            return existing  # type: ignore[no-any-return]

        db_obj = BusinessCollaborator(business_id=business_id, user_id=user_id, role=role)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def create_business_collaborator(self, obj_in: Any) -> BusinessCollaborator:
        data = _to_update_dict(obj_in)
        return self.add_collaborator(
            business_id=data["business_id"],
            user_id=data["user_id"],
            role=data["role"],
        )

    def update_business_collaborator(self, db_obj: BusinessCollaborator, obj_in: Any) -> BusinessCollaborator:
        _apply_updates(db_obj, _to_update_dict(obj_in))
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def remove_collaborator(self, business_id: UUID, user_id: UUID) -> None:
        db_obj = (
            self.db.query(BusinessCollaborator)
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

        self.db.delete(db_obj)
        self.db.commit()

    def delete_business_collaborator(self, id: UUID) -> Optional[BusinessCollaborator]:
        db_obj = self.get_business_collaborator(id=id)
        if not db_obj:
            return None

        if db_obj.role == CollaboratorRole.OWNER:
            raise PermissionError("Cannot remove owner collaborator")

        self.db.delete(db_obj)
        self.db.commit()
        return db_obj

    @staticmethod
    async def handle_business_event(event_type: str, payload: Dict[str, Any]):  # type: ignore
        """Async handler for business events."""
        business = payload.get("business")
        if not business:
            return

        from app.db.database import SessionLocal
        db = SessionLocal()
        try:
            service = BusinessCollaboratorService(db)
            service.add_collaborator(business.id, business.owner_id, CollaboratorRole.OWNER)
            logger.info(f"Automatically added owner as collaborator for business {business.id} via event {event_type}")
        except Exception as e:
            logger.error(f"Failed to auto-add owner collaborator via event handler: {e}")
        finally:
            db.close()

def register_business_collaborator_handlers():  # type: ignore
    """Register BusinessCollaboratorService handlers."""
    dispatcher.subscribe("business.created", BusinessCollaboratorService.handle_business_event)


def get_business_collaborator_service(db: Session = Depends(get_db)) -> BusinessCollaboratorService:
    return BusinessCollaboratorService(db)

# Legacy aliases
def add_collaborator(db: Session, business_id: UUID, user_id: UUID, role: CollaboratorRole) -> BusinessCollaborator:
    return BusinessCollaboratorService(db).add_collaborator(business_id, user_id, role)
