import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

<<<<<<< HEAD
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business.business import BusinessCollaborator
from app.models.enums import CollaboratorRole
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict
from app.core.events import dispatcher
from app.repositories.business_repository import BusinessCollaboratorRepository
=======
from fastapi import Depends
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_db
from app.models.business.business import BusinessCollaborator
from app.models.enums import CollaboratorRole
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict, _apply_updates
from app.core.events import dispatcher
>>>>>>> origin/main

logger = logging.getLogger(__name__)

class BusinessCollaboratorService(BaseService):
    """Service for managing Business Collaborators."""
    db: AsyncSession

<<<<<<< HEAD
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self.repo = BusinessCollaboratorRepository(db)

    async def get_collaborator(self, id: UUID) -> Optional[BusinessCollaborator]:
        return await self.repo.get(id)

    async def get_business_collaborator(self, id: UUID) -> Optional[BusinessCollaborator]:
        return await self.repo.get(id)

    async def get_collaborators(self, business_id: UUID) -> List[BusinessCollaborator]:
        return await self.repo.get_for_business(business_id)

    async def get_business_collaborators(self, skip: int = 0, limit: int = 100) -> List[BusinessCollaborator]:
        return await self.repo.get_all(skip=skip, limit=limit)
=======
    async def get_collaborator(self, id: UUID) -> Optional[BusinessCollaborator]:
        stmt = select(BusinessCollaborator).where(BusinessCollaborator.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


    async def get_business_collaborator(self, id: UUID) -> Optional[BusinessCollaborator]:
        return await self.get_collaborator(id=id)

    async def get_collaborators(self, business_id: UUID) -> List[BusinessCollaborator]:
        stmt = select(BusinessCollaborator).where(BusinessCollaborator.business_id == business_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


    async def get_business_collaborators(self, skip: int = 0, limit: int = 100) -> List[BusinessCollaborator]:
        stmt = select(BusinessCollaborator).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
>>>>>>> origin/main

    async def add_collaborator(
        self,
        business_id: UUID,
        user_id: UUID,
        role: CollaboratorRole,
    ) -> BusinessCollaborator:
<<<<<<< HEAD
        return await self.repo.upsert(business_id, user_id, role)
=======
        stmt = select(BusinessCollaborator).where(
            and_(
                BusinessCollaborator.business_id == business_id,
                BusinessCollaborator.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing is not None:
            existing.role = role
            await self.db.commit()
            await self.db.refresh(existing)
            return existing

        db_obj = BusinessCollaborator(business_id=business_id, user_id=user_id, role=role)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
>>>>>>> origin/main

    async def create_business_collaborator(self, obj_in: Any) -> BusinessCollaborator:
        data = _to_update_dict(obj_in)
        return await self.add_collaborator(
            business_id=data["business_id"],
            user_id=data["user_id"],
            role=data["role"],
        )

    async def update_business_collaborator(self, db_obj: BusinessCollaborator, obj_in: Any) -> BusinessCollaborator:
<<<<<<< HEAD
        return await self.repo.update(db_obj, _to_update_dict(obj_in))

    async def remove_collaborator(self, business_id: UUID, user_id: UUID) -> None:
        existing = await self.repo.get_by_business_and_user(business_id, user_id)
        if existing is None:
            return
        if existing.role == CollaboratorRole.OWNER:
            raise PermissionError("Cannot remove owner collaborator")
        await self.repo.delete(existing.id)

    async def delete_business_collaborator(self, id: UUID) -> Optional[BusinessCollaborator]:
        db_obj = await self.repo.get(id)
        if not db_obj:
            return None
        if db_obj.role == CollaboratorRole.OWNER:
            raise PermissionError("Cannot remove owner collaborator")
        await self.repo.delete(db_obj.id)
=======
        _apply_updates(db_obj, _to_update_dict(obj_in))
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def remove_collaborator(self, business_id: UUID, user_id: UUID) -> None:
        stmt = select(BusinessCollaborator).where(
            and_(
                BusinessCollaborator.business_id == business_id,
                BusinessCollaborator.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        
        if db_obj is None:
            return

        if db_obj.role == CollaboratorRole.OWNER:
            raise PermissionError("Cannot remove owner collaborator")

        await self.db.delete(db_obj)
        await self.db.commit()

    async def delete_business_collaborator(self, id: UUID) -> Optional[BusinessCollaborator]:
        db_obj = await self.get_business_collaborator(id=id)
        if not db_obj:
            return None

        if db_obj.role == CollaboratorRole.OWNER:
            raise PermissionError("Cannot remove owner collaborator")

        await self.db.delete(db_obj)
        await self.db.commit()
>>>>>>> origin/main
        return db_obj

    @staticmethod
    async def handle_business_event(event_type: str, payload: Dict[str, Any]):
        """Async handler for business events."""
        business = payload.get("business")
        if not business:
            return

        from app.db.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            try:
                service = BusinessCollaboratorService(db)
                await service.add_collaborator(business.id, business.owner_id, CollaboratorRole.OWNER)
                logger.info(f"Automatically added owner as collaborator for business {business.id} via event {event_type}")
            except Exception as e:
                logger.error(f"Failed to auto-add owner collaborator via event handler: {e}")

def register_business_collaborator_handlers():
    """Register BusinessCollaboratorService handlers."""
    dispatcher.subscribe("business.created", BusinessCollaboratorService.handle_business_event)


<<<<<<< HEAD
async def get_business_collaborator_service(db: AsyncSession) -> BusinessCollaboratorService:
    return BusinessCollaboratorService(db)

=======
async def get_business_collaborator_service(db: AsyncSession = Depends(get_async_db)) -> BusinessCollaboratorService:
    return BusinessCollaboratorService(db)

# Legacy aliases
async def add_collaborator(db: AsyncSession, business_id: UUID, user_id: UUID, role: CollaboratorRole) -> BusinessCollaborator:
    return await BusinessCollaboratorService(db).add_collaborator(business_id, user_id, role)
>>>>>>> origin/main
