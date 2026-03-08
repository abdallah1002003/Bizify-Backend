import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_db
from app.models import BusinessRoadmap, RoadmapStage
from app.models.enums import RoadmapStageStatus, StageType
from app.services.base_service import BaseService
from app.core.crud_utils import _utc_now
from app.core.events import dispatcher
from app.repositories.business_repository import BusinessRoadmapRepository, RoadmapStageRepository

logger = logging.getLogger(__name__)


class BusinessRoadmapService(BaseService):
    """Service for managing Business Roadmaps and their Stages."""
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.roadmap_repo = BusinessRoadmapRepository(db)
        self.stage_repo = RoadmapStageRepository(db)

    async def _recalculate_roadmap_completion(self, roadmap_id: UUID) -> None:
        stages = await self.stage_repo.get_all_for_roadmap_unordered(roadmap_id)
        
        if not stages:
            return

        completed = sum(1 for stage in stages if stage.status == RoadmapStageStatus.COMPLETED)
        completion = (completed / len(stages)) * 100.0

        roadmap = await self.roadmap_repo.get(roadmap_id)
        if roadmap is None:
            return

        await self.roadmap_repo.update(roadmap, {"completion_percentage": completion})

    # ----------------------------
    # BusinessRoadmap
    # ----------------------------

    async def get_roadmap(self, business_id: UUID) -> Optional[BusinessRoadmap]:
        return await self.roadmap_repo.get_by_business(business_id)


    async def get_business_roadmap(self, id: UUID) -> Optional[BusinessRoadmap]:
        return await self.roadmap_repo.get(id)


    async def get_business_roadmaps(self, skip: int = 0, limit: int = 100) -> List[BusinessRoadmap]:
        return await self.roadmap_repo.get_all(skip=skip, limit=limit)

    async def init_default_roadmap(self, business_id: UUID) -> BusinessRoadmap:
        existing = await self.get_roadmap(business_id=business_id)
        if existing is not None:
            return existing

        db_obj = await self.roadmap_repo.create({"business_id": business_id, "completion_percentage": 0.0})

        # Default first stage.
        await self.add_roadmap_stage(db_obj.id, StageType.READINESS, 0)
        return db_obj

    async def create_business_roadmap(self, obj_in: Any) -> BusinessRoadmap:
        return await self.roadmap_repo.create(obj_in)

    async def update_business_roadmap(self, db_obj: BusinessRoadmap, obj_in: Any) -> BusinessRoadmap:
        return await self.roadmap_repo.update(db_obj, obj_in)

    async def delete_business_roadmap(self, id: UUID) -> Optional[BusinessRoadmap]:
        db_obj = await self.get_business_roadmap(id=id)
        if not db_obj:
            return None

        await self.roadmap_repo.delete(id)
        return db_obj

    # ----------------------------
    # RoadmapStage
    # ----------------------------

    async def get_roadmap_stage(self, id: UUID) -> Optional[RoadmapStage]:
        return await self.stage_repo.get_with_relations(id)

    async def get_roadmap_stages(
        self,
        roadmap_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[RoadmapStage]:
        if roadmap_id is not None:
            return await self.stage_repo.get_for_roadmap(roadmap_id, skip, limit)
        return await self.stage_repo.get_all(skip, limit)

    async def add_roadmap_stage(self, roadmap_id: UUID, stage_type: StageType, order_index: int) -> RoadmapStage:
        return await self.stage_repo.create({
            "roadmap_id": roadmap_id,
            "stage_type": stage_type,
            "order_index": order_index,
            "status": RoadmapStageStatus.PLANNED,
        })

    async def create_roadmap_stage(self, obj_in: Any) -> RoadmapStage:
        return await self.stage_repo.create(obj_in)

    async def update_roadmap_stage(self, db_obj: RoadmapStage, obj_in: Any) -> RoadmapStage:
        updated = await self.stage_repo.update(db_obj, obj_in)

        if updated.status == RoadmapStageStatus.COMPLETED:
            await self._recalculate_roadmap_completion(updated.roadmap_id)

        return updated

    async def delete_roadmap_stage(self, id: UUID) -> Optional[RoadmapStage]:
        db_obj = await self.stage_repo.get(id)
        if not db_obj:
            return None

        roadmap_id = db_obj.roadmap_id
        await self.stage_repo.delete(id)
        await self._recalculate_roadmap_completion(roadmap_id)
        return db_obj

    async def transition_stage(self, stage_id: UUID, new_status: RoadmapStageStatus) -> Optional[RoadmapStage]:
        db_stage = await self.get_roadmap_stage(id=stage_id)
        if db_stage is None:
            return None

        if new_status == RoadmapStageStatus.ACTIVE and db_stage.order_index > 0:
            prev_stage = await self.stage_repo.get_by_order_index(db_stage.roadmap_id, db_stage.order_index - 1)
            
            if prev_stage and prev_stage.status != RoadmapStageStatus.COMPLETED:
                raise ValueError("Prerequisite stage not completed")

        update_data: Dict[str, Any] = {"status": new_status}
        if new_status == RoadmapStageStatus.COMPLETED:
            update_data["completed_at"] = _utc_now()

        updated = await self.stage_repo.update(db_stage, update_data)

        if new_status == RoadmapStageStatus.COMPLETED:
            await self._recalculate_roadmap_completion(updated.roadmap_id)

        return updated

    @staticmethod
    async def handle_business_event(event_type: str, payload: Dict[str, Any]):
        """Async handler for business events."""
        business = payload.get("business")
        if not business:
            return

        from app.db.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            try:
                service = BusinessRoadmapService(db)
                await service.init_default_roadmap(business.id)
                logger.info(f"Automatically initialized roadmap for business {business.id} via event {event_type}")
            except Exception as e:
                logger.error(f"Failed to auto-init roadmap via event handler: {e}")

def register_business_roadmap_handlers():
    """Register BusinessRoadmapService handlers."""
    dispatcher.subscribe("business.created", BusinessRoadmapService.handle_business_event)


async def get_business_roadmap_service(db: AsyncSession = Depends(get_async_db)) -> BusinessRoadmapService:
    return BusinessRoadmapService(db)

# Legacy aliases
async def get_roadmap(db: AsyncSession, business_id: UUID) -> Optional[BusinessRoadmap]:
    """Async alias for get_roadmap."""
    return await BusinessRoadmapService(db).get_roadmap(business_id)

async def init_default_roadmap(db: AsyncSession, business_id: UUID) -> BusinessRoadmap:
    """Async alias for init_default_roadmap."""
    return await BusinessRoadmapService(db).init_default_roadmap(business_id)

async def add_roadmap_stage(db: AsyncSession, roadmap_id: UUID, stage_type: StageType, order_index: int) -> RoadmapStage:
    """Async alias for add_roadmap_stage."""
    return await BusinessRoadmapService(db).add_roadmap_stage(roadmap_id, stage_type, order_index)

async def update_stage_status(db: AsyncSession, stage_id: UUID, new_status: RoadmapStageStatus) -> Optional[RoadmapStage]:
    """Async alias for update_stage_status."""
    return await BusinessRoadmapService(db).transition_stage(stage_id, new_status)

async def transition_stage(db: AsyncSession, stage_id: UUID, new_status: RoadmapStageStatus) -> Optional[RoadmapStage]:
    """Async alias for transition_stage."""
    return await BusinessRoadmapService(db).transition_stage(stage_id, new_status)
