import logging
<<<<<<< HEAD
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BusinessRoadmap, RoadmapStage
from app.models.enums import RoadmapStageStatus, StageType
from app.services.base_service import BaseService
from app.core.crud_utils import _utc_now, _to_update_dict
from app.core.events import dispatcher
from app.repositories.business_repository import BusinessRoadmapRepository, RoadmapStageRepository
=======
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
>>>>>>> origin/main

logger = logging.getLogger(__name__)


class BusinessRoadmapService(BaseService):
    """Service for managing Business Roadmaps and their Stages."""
    db: AsyncSession

<<<<<<< HEAD
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self.roadmap_repo = BusinessRoadmapRepository(db)
        self.stage_repo = RoadmapStageRepository(db)

    async def _recalculate_roadmap_completion(self, roadmap_id: UUID) -> None:
        stages = await self.stage_repo.get_all_for_roadmap_unordered(roadmap_id)
=======
    async def _recalculate_roadmap_completion(self, roadmap_id: UUID) -> None:
        stage_stmt = select(RoadmapStage).where(RoadmapStage.roadmap_id == roadmap_id)
        result = await self.db.execute(stage_stmt)
        stages = list(result.scalars().all())
>>>>>>> origin/main
        
        if not stages:
            return

        completed = sum(1 for stage in stages if stage.status == RoadmapStageStatus.COMPLETED)
        completion = (completed / len(stages)) * 100.0

<<<<<<< HEAD
        roadmap = await self.roadmap_repo.get(roadmap_id)
=======
        roadmap_stmt = select(BusinessRoadmap).where(BusinessRoadmap.id == roadmap_id)
        result = await self.db.execute(roadmap_stmt)
        roadmap = cast(Optional[BusinessRoadmap], result.scalar_one_or_none())
>>>>>>> origin/main
        
        if roadmap is None:
            return

<<<<<<< HEAD
        await self.roadmap_repo.update(roadmap, {"completion_percentage": completion})
=======
        roadmap.completion_percentage = completion
        await self.db.commit()
>>>>>>> origin/main

    # ----------------------------
    # BusinessRoadmap
    # ----------------------------

    async def get_roadmap(self, business_id: UUID) -> Optional[BusinessRoadmap]:
<<<<<<< HEAD
        return await self.roadmap_repo.get_by_business(business_id)

    async def get_business_roadmap(self, id: UUID) -> Optional[BusinessRoadmap]:
        return await self.roadmap_repo.get(id)

    async def get_business_roadmaps(self, skip: int = 0, limit: int = 100) -> List[BusinessRoadmap]:
        return await self.roadmap_repo.get_all(skip=skip, limit=limit)
=======
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
>>>>>>> origin/main

    async def init_default_roadmap(self, business_id: UUID) -> BusinessRoadmap:
        existing = await self.get_roadmap(business_id=business_id)
        if existing is not None:
            return existing

<<<<<<< HEAD
        db_obj = await self.roadmap_repo.create({
            "business_id": business_id,
            "completion_percentage": 0.0
        })
=======
        db_obj = BusinessRoadmap(business_id=business_id, completion_percentage=0.0)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
>>>>>>> origin/main

        # Default first stage.
        await self.add_roadmap_stage(db_obj.id, StageType.READINESS, 0)
        return db_obj

    async def create_business_roadmap(self, obj_in: Any) -> BusinessRoadmap:
<<<<<<< HEAD
        return await self.roadmap_repo.create(_to_update_dict(obj_in))

    async def update_business_roadmap(self, db_obj: BusinessRoadmap, obj_in: Any) -> BusinessRoadmap:
        return await self.roadmap_repo.update(db_obj, obj_in)

    async def delete_business_roadmap(self, id: UUID) -> Optional[BusinessRoadmap]:
        roadmap = await self.roadmap_repo.get(id)
        if roadmap:
            return await self.roadmap_repo.delete(roadmap)
        return None
=======
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
>>>>>>> origin/main

    # ----------------------------
    # RoadmapStage
    # ----------------------------

    async def get_roadmap_stage(self, id: UUID) -> Optional[RoadmapStage]:
<<<<<<< HEAD
        return await self.stage_repo.get_with_relations(id)
=======
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
>>>>>>> origin/main

    async def get_roadmap_stages(
        self,
        roadmap_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[RoadmapStage]:
<<<<<<< HEAD
        if roadmap_id is None:
            return await self.stage_repo.get_all(skip=skip, limit=limit)
        return await self.stage_repo.get_for_roadmap(roadmap_id, skip=skip, limit=limit)

    async def add_roadmap_stage(self, roadmap_id: UUID, stage_type: StageType, order_index: int) -> RoadmapStage:
        return await self.stage_repo.create({
            "roadmap_id": roadmap_id,
            "stage_type": stage_type,
            "order_index": order_index,
            "status": RoadmapStageStatus.PLANNED,
        })

    async def create_roadmap_stage(self, obj_in: Any) -> RoadmapStage:
        return await self.stage_repo.create(_to_update_dict(obj_in))

    async def update_roadmap_stage(self, db_obj: RoadmapStage, obj_in: Any) -> RoadmapStage:
        updated = await self.stage_repo.update(db_obj, obj_in)
        if updated.status == RoadmapStageStatus.COMPLETED:
            await self._recalculate_roadmap_completion(updated.roadmap_id)
        return updated

    async def delete_roadmap_stage(self, id: UUID) -> Optional[RoadmapStage]:
        stage = await self.stage_repo.get(id)
        if stage:
            roadmap_id = stage.roadmap_id
            deleted_stage = await self.stage_repo.delete(stage)
            await self._recalculate_roadmap_completion(roadmap_id)
            return deleted_stage
        return None
=======
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
>>>>>>> origin/main

    async def transition_stage(self, stage_id: UUID, new_status: RoadmapStageStatus) -> Optional[RoadmapStage]:
        db_stage = await self.get_roadmap_stage(id=stage_id)
        if db_stage is None:
            return None

        if new_status == RoadmapStageStatus.ACTIVE and db_stage.order_index > 0:
<<<<<<< HEAD
            prev_stage = await self.stage_repo.get_by_order_index(
                db_stage.roadmap_id, db_stage.order_index - 1
            )
=======
            stmt = select(RoadmapStage).where(
                and_(
                    RoadmapStage.roadmap_id == db_stage.roadmap_id,
                    RoadmapStage.order_index == db_stage.order_index - 1,
                )
            )
            result = await self.db.execute(stmt)
            prev_stage = cast(Optional[RoadmapStage], result.scalar_one_or_none())
>>>>>>> origin/main
            
            if prev_stage and prev_stage.status != RoadmapStageStatus.COMPLETED:
                raise ValueError("Prerequisite stage not completed")

<<<<<<< HEAD
        update_data: dict[str, Any] = {"status": new_status}
        if new_status == RoadmapStageStatus.COMPLETED:
            update_data["completed_at"] = _utc_now()

        updated_stage = await self.stage_repo.update(db_stage, update_data)

        if new_status == RoadmapStageStatus.COMPLETED:
            await self._recalculate_roadmap_completion(updated_stage.roadmap_id)

        return updated_stage
=======
        db_stage.status = new_status
        if new_status == RoadmapStageStatus.COMPLETED:
            db_stage.completed_at = _utc_now()

        await self.db.commit()
        await self.db.refresh(db_stage)

        if new_status == RoadmapStageStatus.COMPLETED:
            await self._recalculate_roadmap_completion(db_stage.roadmap_id)

        return db_stage
>>>>>>> origin/main

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


<<<<<<< HEAD
async def get_business_roadmap_service(db: AsyncSession) -> BusinessRoadmapService:
    return BusinessRoadmapService(db)

=======
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
>>>>>>> origin/main
