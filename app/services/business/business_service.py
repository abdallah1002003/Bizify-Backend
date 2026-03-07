from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business.business import Business
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict
from app.services.business.business_roadmap import BusinessRoadmapService
from app.services.business.business_collaborator import BusinessCollaboratorService
from app.repositories.business_repository import BusinessRepository

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
        db_obj = await self.repo.create(_to_update_dict(obj_in))

        # Restore synchronous side-effect: default roadmap
        await self.roadmap.init_default_roadmap(db_obj.id)
        return db_obj

    async def update_business(self, db_obj: Business, obj_in: Any) -> Business:
        return await self.repo.update(db_obj, _to_update_dict(obj_in))

    async def delete_business(self, id: UUID) -> Optional[Business]:
        return await self.repo.delete(id)

    async def update_business_stage(self, business_id: UUID, new_stage: Any) -> Optional[Business]:
        db_obj = await self.repo.get_with_relations(business_id)
        if db_obj is None:
            return None
        return await self.repo.update(db_obj, {"stage": new_stage})


async def get_business_service(
    db: AsyncSession,
    roadmap: Optional[BusinessRoadmapService] = None,
    collaborator: Optional[BusinessCollaboratorService] = None,
) -> BusinessService:
    """Dependency provider for BusinessService."""
    roadmap = roadmap or BusinessRoadmapService(db)
    collaborator = collaborator or BusinessCollaboratorService(db)
    return BusinessService(db, roadmap, collaborator)


