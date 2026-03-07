from typing import Any, List, Optional
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_db
from app.models.business.business import Business, BusinessCollaborator
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict, _apply_updates
from app.services.business.business_roadmap import BusinessRoadmapService, get_business_roadmap_service
from app.services.business.business_collaborator import BusinessCollaboratorService, get_business_collaborator_service

class BusinessService(BaseService):
    """Main service for managing Businesses, delegating to roadmap and collaborator services."""
    db: AsyncSession

    def __init__(
        self,
        db: AsyncSession,
        roadmap_service: BusinessRoadmapService,
        collaborator_service: BusinessCollaboratorService
    ):
        super().__init__(db)
        self.roadmap = roadmap_service
        self.collaborator = collaborator_service

    # ----------------------------
    # Business CRUD
    # ----------------------------

    async def get_business(self, id: UUID) -> Optional[Business]:
        stmt = select(Business).where(Business.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


    async def get_businesses(
        self,
        skip: int = 0,
        limit: int = 100,
        owner_id: Optional[UUID] = None,
    ) -> List[Business]:
        """Retrieve businesses with optional owner filtering."""
        from sqlalchemy.orm import selectinload
        
        stmt = select(Business).options(
            selectinload(Business.owner),
            selectinload(Business.collaborators).selectinload(BusinessCollaborator.user),
            selectinload(Business.roadmap)
        )
        if owner_id is not None:
            stmt = stmt.where(Business.owner_id == owner_id)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


    async def create_business(self, obj_in: Any) -> Business:
        """Create a new business and emit creation event."""
        db_obj = Business(**_to_update_dict(obj_in))
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        # Restore synchronous side-effect: default roadmap
        await self.roadmap.init_default_roadmap(db_obj.id)
        return db_obj

    async def update_business(self, db_obj: Business, obj_in: Any) -> Business:
        _apply_updates(db_obj, _to_update_dict(obj_in))
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete_business(self, id: UUID) -> Optional[Business]:
        db_obj = await self.get_business(id=id)
        if not db_obj:
            return None

        await self.db.delete(db_obj)
        await self.db.commit()
        return db_obj

    async def update_business_stage(self, business_id: UUID, new_stage: Any) -> Optional[Business]:
        db_obj = await self.get_business(business_id)
        if db_obj is None:
            return None
        db_obj.stage = new_stage
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj


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
