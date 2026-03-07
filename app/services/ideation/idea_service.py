from typing import Any, List, Optional
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_db
from app.models.ideation.idea import Idea, IdeaAccess
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict, _apply_updates
from app.services.ideation.idea_access import IdeaAccessService, get_idea_access_service
from app.services.ideation.idea_version import IdeaVersionService, get_idea_version_service

class IdeaService(BaseService):
    """Main service for managing Ideas, delegating to access and version services."""
    db: AsyncSession

    def __init__(
        self,
        db: AsyncSession,
        access_service: IdeaAccessService,
        version_service: IdeaVersionService
    ):
        super().__init__(db)
        self.access = access_service
        self.version = version_service

    # ----------------------------
    # Idea CRUD
    # ----------------------------

    async def get_idea(self, id: UUID, user_id: Optional[UUID] = None) -> Optional[Idea]:
        """Retrieve an idea by ID with optional access control."""
        stmt = select(Idea).where(Idea.id == id)
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        
        if db_obj is None:
            return None

        if user_id is not None and not await self.access.check_idea_access(id, user_id, "view"):
            return None

        return db_obj


    async def get_ideas(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[UUID] = None,
    ) -> List[Idea]:
        """Retrieve ideas with optional user-based filtering."""
        from sqlalchemy.orm import selectinload
        
        stmt = select(Idea).options(
            selectinload(Idea.owner),
            selectinload(Idea.business)
        )
        if user_id is not None:
            stmt = stmt.outerjoin(IdeaAccess).where(
                or_(Idea.owner_id == user_id, IdeaAccess.user_id == user_id)
            )
        stmt = stmt.distinct().offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


    async def create_idea(self, obj_in: Any) -> Idea:
        """Create a new idea and its initial version snapshot."""
        db_obj = Idea(**_to_update_dict(obj_in))
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        # Restore synchronous side-effect: initial snapshot
        await self.version.create_idea_snapshot(db_obj)
        return db_obj

    async def update_idea(self, db_obj: Idea, obj_in: Any, performer_id: Optional[UUID] = None) -> Idea:
        """Update an idea and create a new version snapshot if major fields changed."""
        if performer_id is not None and not await self.access.check_idea_access(db_obj.id, performer_id, "edit"):
            raise PermissionError("Not authorized to edit this idea")

        update_data = _to_update_dict(obj_in)
        major_changed = any(field in update_data for field in ("title", "description", "status"))

        _apply_updates(db_obj, update_data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        # Restore synchronous side-effect: snapshot on major change
        if major_changed:
            await self.version.create_idea_snapshot(db_obj, created_by=performer_id)

        return db_obj

    async def delete_idea(self, id: UUID) -> Optional[Idea]:
        """Delete an idea from the system."""
        stmt = select(Idea).where(Idea.id == id)
        result = await self.db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        
        if not db_obj:
            return None

        await self.db.delete(db_obj)
        await self.db.commit()
        return db_obj

    async def check_idea_access(self, idea_id: UUID, user_id: UUID, required_perm: str = "view") -> bool:
        """Helper to expose access check via this service."""
        return await self.access.check_idea_access(idea_id, user_id, required_perm)


async def get_idea_service(
    db: AsyncSession = Depends(get_async_db),
    access: IdeaAccessService = Depends(get_idea_access_service),
    version: IdeaVersionService = Depends(get_idea_version_service),
) -> IdeaService:
    """Dependency provider for IdeaService."""
    return IdeaService(db, access, version)


# Legacy aliases (Supports older tests calling functions directly)
async def get_idea_service_manual(db: AsyncSession) -> IdeaService:
    """Helper to manually instantiate IdeaService for legacy calls."""
    from app.services.ideation.idea_access import IdeaAccessService
    from app.services.ideation.idea_version import IdeaVersionService
    return IdeaService(
        db=db,
        access_service=IdeaAccessService(db),
        version_service=IdeaVersionService(db)
    )

async def get_idea(db: AsyncSession, id: UUID, user_id: Optional[UUID] = None) -> Optional[Idea]:
    """Legacy async alias for retrieving an idea."""
    service = await get_idea_service_manual(db)
    return await service.get_idea(id, user_id)

async def create_idea(db: AsyncSession, obj_in: Any) -> Idea:
    """Legacy async alias for creating an idea."""
    service = await get_idea_service_manual(db)
    return await service.create_idea(obj_in)

async def update_idea(db: AsyncSession, db_obj: Idea, obj_in: Any, performer_id: Optional[UUID] = None) -> Idea:
    """Legacy async alias for updating an idea."""
    service = await get_idea_service_manual(db)
    return await service.update_idea(db_obj, obj_in, performer_id)

async def check_idea_access(db: AsyncSession, idea_id: UUID, user_id: UUID, required_perm: str = "view") -> bool:
    """Legacy async alias for checking idea access."""
    service = await get_idea_service_manual(db)
    return await service.check_idea_access(idea_id, user_id, required_perm)

async def delete_idea(db: AsyncSession, id: UUID) -> Optional[Idea]:
    """Legacy async alias for deleting an idea."""
    service = await get_idea_service_manual(db)
    return await service.delete_idea(id)
