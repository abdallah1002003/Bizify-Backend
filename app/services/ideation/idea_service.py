from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ideation.idea import Idea
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict
from app.services.ideation.idea_access import IdeaAccessService
from app.services.ideation.idea_version import IdeaVersionService
from app.repositories.idea_repository import IdeaRepository

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
        self.repo = IdeaRepository(db)

    # ----------------------------
    # Idea CRUD
    # ----------------------------

    async def get_idea(self, id: UUID, user_id: Optional[UUID] = None) -> Optional[Idea]:
        """Retrieve an idea by ID with optional access control."""
        db_obj = await self.repo.get(id)

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
        return await self.repo.get_all_filtered(user_id=user_id, skip=skip, limit=limit)


    async def create_idea(self, obj_in: Any) -> Idea:
        """Create a new idea and its initial version snapshot."""
        db_obj = await self.repo.create(_to_update_dict(obj_in))

        # Restore synchronous side-effect: initial snapshot
        await self.version.create_idea_snapshot(db_obj)
        return db_obj

    async def update_idea(self, db_obj: Idea, obj_in: Any, performer_id: Optional[UUID] = None) -> Idea:
        """Update an idea and create a new version snapshot if major fields changed."""
        if performer_id is not None and not await self.access.check_idea_access(db_obj.id, performer_id, "edit"):
            raise PermissionError("Not authorized to edit this idea")

        update_data = _to_update_dict(obj_in)
        major_changed = any(field in update_data for field in ("title", "description", "status"))

        db_obj = await self.repo.update(db_obj, update_data)

        # Restore synchronous side-effect: snapshot on major change
        if major_changed:
            await self.version.create_idea_snapshot(db_obj, created_by=performer_id)

        return db_obj

    async def delete_idea(self, id: UUID) -> Optional[Idea]:
        """Delete an idea from the system."""
        return await self.repo.delete(id)

    async def check_idea_access(self, idea_id: UUID, user_id: UUID, required_perm: str = "view") -> bool:
        """Helper to expose access check via this service."""
        return await self.access.check_idea_access(idea_id, user_id, required_perm)


async def get_idea_service(
    db: AsyncSession,
    access: Optional[IdeaAccessService] = None,
    version: Optional[IdeaVersionService] = None,
) -> IdeaService:
    """Dependency provider for IdeaService."""
    access = access or IdeaAccessService(db)
    version = version or IdeaVersionService(db)
    return IdeaService(db, access, version)


