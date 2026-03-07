from typing import Any, Dict, List, Optional
from uuid import UUID


from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ideation.idea import IdeaAccess
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict
from app.repositories.idea_repository import IdeaAccessRepository, IdeaRepository

class IdeaAccessService(BaseService):
    """Service for managing access permissions to Ideas."""
    db: AsyncSession

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self.repo = IdeaAccessRepository(db)
        self.idea_repo = IdeaRepository(db)

    async def check_idea_access(self, idea_id: UUID, user_id: UUID, required_perm: str = "view") -> bool:
        """Check if a user has specific permissions for an idea."""
        idea = await self.idea_repo.get(idea_id)
        
        if idea is None:
            return False

        if idea.owner_id == user_id:
            return True

        access = await self.repo.get_by_idea_and_user(idea_id, user_id)
        
        if access is None:
            return False

        if required_perm == "view":
            return True
        if required_perm == "edit":
            return bool(access.can_edit)
        if required_perm == "delete":
            return bool(access.can_delete)
        if required_perm == "experiment":
            return bool(access.can_experiment)

        return False

    async def grant_access(self, idea_id: UUID, user_id: UUID, permissions: Dict[str, bool]) -> IdeaAccess:
        """Grant or update access permissions for a user on an idea.
        
        Uses create_safe() to handle concurrent requests attempting to grant access
        to the same user (uniqueness constraint on idea_id, user_id).
        """
        access = await self.repo.get_by_idea_and_user(idea_id, user_id)
        
        if access is None:
            # Try to create safely, handling concurrent inserts
            created = await self.repo.create_safe({
                "idea_id": idea_id,
                "user_id": user_id,
                "can_edit": permissions.get("edit", False),
                "can_delete": permissions.get("delete", False),
                "can_experiment": permissions.get("experiment", False),
            }, auto_commit=True)
            
            if created is not None:
                return created
            
            # If create_safe returned None, another transaction inserted the access.
            # Fetch it and update with the provided permissions.
            access = await self.repo.get_by_idea_and_user(idea_id, user_id)
            if access is not None:
                return await self.repo.update(access, {
                    "can_edit": permissions.get("edit", access.can_edit),
                    "can_delete": permissions.get("delete", access.can_delete),
                    "can_experiment": permissions.get("experiment", access.can_experiment),
                })
            
            # This should not happen in practice. Raise an error.
            raise RuntimeError(f"Failed to grant access for user {user_id} on idea {idea_id}")
        else:
            return await self.repo.update(access, {
                "can_edit": permissions.get("edit", access.can_edit),
                "can_delete": permissions.get("delete", access.can_delete),
                "can_experiment": permissions.get("experiment", access.can_experiment),
            })


    async def get_idea_access(self, id: UUID) -> Optional[IdeaAccess]:
        return await self.repo.get(id)

    async def get_idea_accesses(self, skip: int = 0, limit: int = 100) -> List[IdeaAccess]:
        return await self.repo.get_all(skip=skip, limit=limit)

    async def get_idea_accesses_by_owner(self, owner_id: UUID, skip: int = 0, limit: int = 100) -> List[IdeaAccess]:
        return await self.repo.get_for_owner(owner_id, skip=skip, limit=limit)

    async def create_idea_access(self, obj_in: Any) -> IdeaAccess:
        """Create an idea access record.
        
        Uses create_safe() to handle concurrent requests attempting to create
        the same access record (uniqueness constraint on idea_id, user_id).
        """
        data = _to_update_dict(obj_in)
        created = await self.repo.create_safe(data, auto_commit=True)
        if created is not None:
            return created
        
        # If create_safe returned None, another transaction inserted this access.
        # Fetch and return it.
        idea_id = data.get("idea_id")
        user_id = data.get("user_id")
        existing = await self.repo.get_by_idea_and_user(idea_id, user_id)
        if existing is not None:
            return existing
        
        # This should not happen in practice. Raise an error.
        raise RuntimeError(f"Failed to create access for user {user_id} on idea {idea_id}")

    async def update_idea_access(self, db_obj: IdeaAccess, obj_in: Any) -> IdeaAccess:
        return await self.repo.update(db_obj, _to_update_dict(obj_in))

    async def delete_idea_access(self, id: UUID) -> Optional[IdeaAccess]:
        return await self.repo.delete(id)


async def get_idea_access_service(db: AsyncSession) -> IdeaAccessService:
    return IdeaAccessService(db)

