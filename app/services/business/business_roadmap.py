import logging
from typing import Any, Dict, List, Optional, cast
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_db
from app.models import BusinessRoadmap, RoadmapStage
from app.models.enums import RoadmapStageStatus, StageType
from app.services.base_service import BaseService
from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates
from app.core.events import dispatcher

logger = logging.getLogger(__name__)


class BusinessRoadmapService(BaseService):
    """Service for managing Business Roadmaps and their Stages."""
    db: AsyncSession

    async def _recalculate_roadmap_completion(self, roadmap_id: UUID) -> None:
        stage_stmt = select(RoadmapStage).where(RoadmapStage.roadmap_id == roadmap_id)
        result = await self.db.execute(stage_stmt)
        stages = list(result.scalars().all())
        
        if not stages:
            return

        completed = sum(1 for stage in stages if stage.status == RoadmapStageStatus.COMPLETED)
        completion = (completed / len(stages)) * 100.0

        roadmap_stmt = select(BusinessRoadmap).where(BusinessRoadmap.id == roadmap_id)
        result = await self.db.execute(roadmap_stmt)
        roadmap = cast(Optional[BusinessRoadmap], result.scalar_one_or_none())
        
        if roadmap is None:
            return

        roadmap.completion_percentage = completion
        await self.db.commit()

    # ----------------------------
    # BusinessRoadmap
    # ----------------------------

    async def get_roadmap(self, business_id: UUID) -> Optional[BusinessRoadmap]:
        stmt = select(BusinessRoadmap).where(BusinessRoadmap.business_id == business_id)
        result = await self.db.execute(stmt)
        return cast(Optional[BusinessRoadmap], result.scalar_one_or_none())


    async def get_business_roadmap(self, id: UUID) -> Optional[BusinessRoadmap]:
        stmt = select(BusinessRoadmap).where(BusinessRoadmap.id == id)
        result = await self.db.execute(stmt)
        return cast(Optional[BusinessRoadmap], result.scalar_one_or_none())


    async def get_business_roadmaps(self, skip: int = 0, limit: int = 100) -> List[BusinessRoadmap]:
        stmt = select(BusinessRoadmap).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def init_default_roadmap(self, business_id: UUID) -> BusinessRoadmap:
        existing = await self.get_roadmap(business_id=business_id)
        if existing is not None:
            return existing

        db_obj = BusinessRoadmap(business_id=business_id, completion_percentage=0.0)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        # Default first stage.
        await self.add_roadmap_stage(db_obj.id, StageType.READINESS, 0)
        return db_obj

    async def create_business_roadmap(self, obj_in: Any) -> BusinessRoadmap:
        db_obj = BusinessRoadmap(**_to_update_dict(obj_in))
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update_business_roadmap(self, db_obj: BusinessRoadmap, obj_in: Any) -> BusinessRoadmap:
        _apply_updates(db_obj, _to_update_dict(obj_in))
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete_business_roadmap(self, id: UUID) -> Optional[BusinessRoadmap]:
        db_obj = await self.get_business_roadmap(id=id)
        if not db_obj:
            return None

        await self.db.delete(db_obj)
        await self.db.commit()
        return db_obj

    # ----------------------------
    # RoadmapStage
    # ----------------------------

    async def get_roadmap_stage(self, id: UUID) -> Optional[RoadmapStage]:
        from sqlalchemy.orm import joinedload
        from app.models import BusinessRoadmap
        stmt = (
            select(RoadmapStage)
            .options(
                joinedload(RoadmapStage.roadmap).joinedload(BusinessRoadmap.business)
            )
            .where(RoadmapStage.id == id)
        )
        result = await self.db.execute(stmt)
        return cast(Optional[RoadmapStage], result.scalar_one_or_none())

    async def get_roadmap_stages(
        self,
        roadmap_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[RoadmapStage]:
        stmt = select(RoadmapStage)
        if roadmap_id is not None:
            stmt = stmt.where(RoadmapStage.roadmap_id == roadmap_id)
        stmt = stmt.order_by(RoadmapStage.order_index.asc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def add_roadmap_stage(self, roadmap_id: UUID, stage_type: StageType, order_index: int) -> RoadmapStage:
        db_stage = RoadmapStage(
            roadmap_id=roadmap_id,
            stage_type=stage_type,
            order_index=order_index,
            status=RoadmapStageStatus.PLANNED,
        )
        self.db.add(db_stage)
        await self.db.commit()
        await self.db.refresh(db_stage)
        return db_stage

    async def create_roadmap_stage(self, obj_in: Any) -> RoadmapStage:
        db_obj = RoadmapStage(**_to_update_dict(obj_in))
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update_roadmap_stage(self, db_obj: RoadmapStage, obj_in: Any) -> RoadmapStage:
        _apply_updates(db_obj, _to_update_dict(obj_in))
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        if db_obj.status == RoadmapStageStatus.COMPLETED:
            await self._recalculate_roadmap_completion(db_obj.roadmap_id)

        return db_obj

    async def delete_roadmap_stage(self, id: UUID) -> Optional[RoadmapStage]:
        db_obj = await self.get_roadmap_stage(id=id)
        if not db_obj:
            return None

        roadmap_id = db_obj.roadmap_id
        await self.db.delete(db_obj)
        await self.db.commit()
        await self._recalculate_roadmap_completion(roadmap_id)
        return db_obj

    async def transition_stage(self, stage_id: UUID, new_status: RoadmapStageStatus) -> Optional[RoadmapStage]:
        db_stage = await self.get_roadmap_stage(id=stage_id)
        if db_stage is None:
            return None

        if new_status == RoadmapStageStatus.ACTIVE and db_stage.order_index > 0:
            stmt = select(RoadmapStage).where(
                and_(
                    RoadmapStage.roadmap_id == db_stage.roadmap_id,
                    RoadmapStage.order_index == db_stage.order_index - 1,
                )
            )
            result = await self.db.execute(stmt)
            prev_stage = cast(Optional[RoadmapStage], result.scalar_one_or_none())
            
            if prev_stage and prev_stage.status != RoadmapStageStatus.COMPLETED:
                raise ValueError("Prerequisite stage not completed")

        db_stage.status = new_status
        if new_status == RoadmapStageStatus.COMPLETED:
            db_stage.completed_at = _utc_now()

        await self.db.commit()
        await self.db.refresh(db_stage)

        if new_status == RoadmapStageStatus.COMPLETED:
            await self._recalculate_roadmap_completion(db_stage.roadmap_id)

        return db_stage

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
