import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_db
from app.models import IdeaVersion
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict, _apply_updates
from app.core.events import dispatcher

logger = logging.getLogger(__name__)


class IdeaVersionService(BaseService):
    """Service for managing snapshots/versions of Ideas."""
    db: AsyncSession

    async def create_idea_snapshot(self, idea: Any, created_by: Optional[UUID] = None) -> IdeaVersion:
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
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def get_idea_version(self, id: UUID) -> Optional[IdeaVersion]:
        stmt = select(IdeaVersion).where(IdeaVersion.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


    async def get_idea_versions(
        self,
        idea_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[IdeaVersion]:
        stmt = select(IdeaVersion)
        if idea_id is not None:
            stmt = stmt.where(IdeaVersion.idea_id == idea_id)
        stmt = stmt.order_by(IdeaVersion.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


    async def create_idea_version(self, obj_in: Any) -> IdeaVersion:
        db_obj = IdeaVersion(**_to_update_dict(obj_in))
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update_idea_version(self, db_obj: IdeaVersion, obj_in: Any) -> IdeaVersion:
        _apply_updates(db_obj, _to_update_dict(obj_in))
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete_idea_version(self, id: UUID) -> Optional[IdeaVersion]:
        db_obj = await self.get_idea_version(id=id)
        if not db_obj:
            return None

        await self.db.delete(db_obj)
        await self.db.commit()
        return db_obj

    @staticmethod
    async def handle_idea_event(event_type: str, payload: Dict[str, Any]):
        """Async handler for idea events."""
        idea = payload.get("idea")
        performer_id = payload.get("performer_id")
        
        if not idea:
            return

        # We need a fresh DB session for the async handler
        from app.db.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            try:
                service = IdeaVersionService(db)
                await service.create_idea_snapshot(idea, created_by=performer_id)
                logger.info(f"Automatically created snapshot for idea {idea.id} via event {event_type}")
            except Exception as e:
                logger.error(f"Failed to create snapshot via event handler: {e}")


def register_idea_version_handlers():
    """Register IdeaVersionService handlers to the event dispatcher."""
    dispatcher.subscribe("idea.created", IdeaVersionService.handle_idea_event)
    dispatcher.subscribe("idea.updated", IdeaVersionService.handle_idea_event)


async def get_idea_version_service(db: AsyncSession = Depends(get_async_db)) -> IdeaVersionService:
    return IdeaVersionService(db)

# Legacy aliases
async def create_idea_snapshot(db: AsyncSession, idea: Any, created_by: Optional[UUID] = None) -> IdeaVersion:
    return await IdeaVersionService(db).create_idea_snapshot(idea, created_by)
