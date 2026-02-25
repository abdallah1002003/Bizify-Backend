import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import IdeaVersion
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict, _apply_updates
from app.core.events import dispatcher

logger = logging.getLogger(__name__)


class IdeaVersionService(BaseService):
    """Service for managing snapshots/versions of Ideas."""

    def create_idea_snapshot(self, idea: Any, created_by: Optional[UUID] = None) -> IdeaVersion:
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
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get_idea_version(self, id: UUID) -> Optional[IdeaVersion]:
        return self.db.query(IdeaVersion).filter(IdeaVersion.id == id).first()  # type: ignore[no-any-return]

    def get_idea_versions(
        self,
        idea_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[IdeaVersion]:
        query = self.db.query(IdeaVersion)
        if idea_id is not None:
            query = query.filter(IdeaVersion.idea_id == idea_id)
        return query.order_by(IdeaVersion.created_at.desc()).offset(skip).limit(limit).all()  # type: ignore[no-any-return]

    def create_idea_version(self, obj_in: Any) -> IdeaVersion:
        db_obj = IdeaVersion(**_to_update_dict(obj_in))
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update_idea_version(self, db_obj: IdeaVersion, obj_in: Any) -> IdeaVersion:
        _apply_updates(db_obj, _to_update_dict(obj_in))
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete_idea_version(self, id: UUID) -> Optional[IdeaVersion]:
        db_obj = self.get_idea_version(id=id)
        if not db_obj:
            return None

        self.db.delete(db_obj)
        self.db.commit()
        return db_obj

    @staticmethod
    async def handle_idea_event(event_type: str, payload: Dict[str, Any]):  # type: ignore
        """Async handler for idea events."""
        idea = payload.get("idea")
        performer_id = payload.get("performer_id")
        
        if not idea:
            return

        # We need a fresh DB session for the async handler
        from app.db.database import SessionLocal
        db = SessionLocal()
        try:
            service = IdeaVersionService(db)
            service.create_idea_snapshot(idea, created_by=performer_id)
            logger.info(f"Automatically created snapshot for idea {idea.id} via event {event_type}")
        except Exception as e:
            logger.error(f"Failed to create snapshot via event handler: {e}")
        finally:
            db.close()

def register_idea_version_handlers():  # type: ignore
    """Register IdeaVersionService handlers to the event dispatcher."""
    dispatcher.subscribe("idea.created", IdeaVersionService.handle_idea_event)
    dispatcher.subscribe("idea.updated", IdeaVersionService.handle_idea_event)


def get_idea_version_service(db: Session = Depends(get_db)) -> IdeaVersionService:
    return IdeaVersionService(db)

# Legacy aliases
def create_idea_snapshot(db: Session, idea: Any, created_by: Optional[UUID] = None) -> IdeaVersion:
    return IdeaVersionService(db).create_idea_snapshot(idea, created_by)
