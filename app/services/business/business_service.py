from typing import Any, List, Optional
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_db
from app.models.business.business import Business
from app.services.base_service import BaseService
from app.services.business.business_roadmap import BusinessRoadmapService, get_business_roadmap_service
from app.services.business.business_collaborator import BusinessCollaboratorService, get_business_collaborator_service

from app.repositories.business_repository import BusinessRepository


class BusinessService(BaseService):
    """Main service for managing Businesses, delegating to roadmap and collaborator services."""

    def __init__(
        self,
        db: AsyncSession,
        roadmap_service: Optional[BusinessRoadmapService] = None,
        collaborator_service: Optional[BusinessCollaboratorService] = None
    ):
        super().__init__(db)
        self.roadmap = roadmap_service or BusinessRoadmapService(db)
        self.collaborator = collaborator_service or BusinessCollaboratorService(db)
        self.repo = BusinessRepository(db)

    # ----------------------------
    # Business CRUD
    # ----------------------------

    async def get_business(self, id: UUID) -> Optional[Business]:
        return await self.repo.get_with_relations(id)


    async def get_businesses(
        self,
        skip: int = 0,
        limit: int = 100,
        owner_id: Optional[UUID] = None,
    ) -> List[Business]:
        """Retrieve businesses with optional owner filtering."""
        return await self.repo.get_all_filtered(owner_id=owner_id, skip=skip, limit=limit)


    async def create_business(self, obj_in: Any) -> Business:
        """Create a new business and emit creation event."""
        db_obj = await self.repo.create(obj_in)
        # Restore synchronous side-effect: default roadmap
        await self.roadmap.init_default_roadmap(db_obj.id)
        return db_obj

    async def update_business(self, db_obj: Business, obj_in: Any) -> Business:
        return await self.repo.update(db_obj, obj_in)

    async def delete_business(self, id: UUID) -> Optional[Business]:
        return await self.repo.delete(id)

    async def update_business_stage(self, business_id: UUID, new_stage: Any) -> Optional[Business]:
        db_obj = await self.get_business(business_id)
        if db_obj is None:
            return None
        return await self.repo.update(db_obj, {"stage": new_stage})


async def get_business_service(
    db: AsyncSession = Depends(get_async_db),
    roadmap: BusinessRoadmapService = Depends(get_business_roadmap_service),
    collaborator: BusinessCollaboratorService = Depends(get_business_collaborator_service),
) -> BusinessService:
    """Dependency provider for BusinessService."""
    return BusinessService(db, roadmap, collaborator)


# Legacy aliases (Supports older tests calling functions directly)
async def get_business_service_manual(db: AsyncSession) -> BusinessService:
    """Manual provider for BusinessService, useful for testing."""
    from app.services.business.business_roadmap import BusinessRoadmapService
    from app.services.business.business_collaborator import BusinessCollaboratorService
    return BusinessService(
        db=db,
        roadmap_service=BusinessRoadmapService(db),
        collaborator_service=BusinessCollaboratorService(db)
    )

async def get_business(db: AsyncSession, id: UUID) -> Optional[Business]:
    service = await get_business_service_manual(db)
    return await service.get_business(id)

async def create_business(db: AsyncSession, obj_in: Any) -> Business:
    service = await get_business_service_manual(db)
    return await service.create_business(obj_in)

async def update_business(db: AsyncSession, db_obj: Business, obj_in: Any) -> Business:
    service = await get_business_service_manual(db)
    return await service.update_business(db_obj, obj_in)

async def delete_business(db: AsyncSession, id: UUID) -> Optional[Business]:
    service = await get_business_service_manual(db)
    return await service.delete_business(id)
