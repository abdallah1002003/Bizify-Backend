from typing import Any, Dict, List, Optional, cast
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_db
from app.models.ideation.idea import IdeaAccess
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict, _apply_updates

class IdeaAccessService(BaseService):
    """Service for managing access permissions to Ideas."""
    db: AsyncSession

    async def check_idea_access(self, idea_id: UUID, user_id: UUID, required_perm: str = "view") -> bool:
        """Check if a user has specific permissions for an idea."""
        from app.models.ideation.idea import Idea
        
        # Using select() for AsyncSession compatibility
        stmt = select(Idea).where(Idea.id == idea_id)
        result = await self.db.execute(stmt)
        idea = cast(Optional[Idea], result.scalar_one_or_none())
        
        if idea is None:
            return False

        if idea.owner_id == user_id:
            return True

        access_stmt = select(IdeaAccess).where(
            and_(IdeaAccess.idea_id == idea_id, IdeaAccess.user_id == user_id)
        )
        result = await self.db.execute(access_stmt)
        access = cast(Optional[IdeaAccess], result.scalar_one_or_none())
        
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
        """Grant or update access permissions for a user on an idea."""
        stmt = select(IdeaAccess).where(
            and_(IdeaAccess.idea_id == idea_id, IdeaAccess.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        access = result.scalar_one_or_none()
        
        if access is None:
            access = IdeaAccess(
                idea_id=idea_id,
                user_id=user_id,
                can_edit=permissions.get("edit", False),
                can_delete=permissions.get("delete", False),
                can_experiment=permissions.get("experiment", False),
            )
            self.db.add(access)
        else:
            access.can_edit = permissions.get("edit", access.can_edit)
            access.can_delete = permissions.get("delete", access.can_delete)
            access.can_experiment = permissions.get("experiment", access.can_experiment)

        await self.db.commit()
        await self.db.refresh(access)
        return access


    async def get_idea_access(self, id: UUID) -> Optional[IdeaAccess]:
        stmt = select(IdeaAccess).where(IdeaAccess.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


    async def get_idea_accesses(self, skip: int = 0, limit: int = 100) -> List[IdeaAccess]:
        stmt = select(IdeaAccess).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_idea_accesses_by_owner(self, owner_id: UUID, skip: int = 0, limit: int = 100) -> List[IdeaAccess]:
        from app.models.ideation.idea import Idea
        stmt = (
            select(IdeaAccess)
            .join(Idea, IdeaAccess.idea_id == Idea.id)
            .where(Idea.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_idea_access(self, obj_in: Any) -> IdeaAccess:
        db_obj = IdeaAccess(**_to_update_dict(obj_in))
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update_idea_access(self, db_obj: IdeaAccess, obj_in: Any) -> IdeaAccess:
        _apply_updates(db_obj, _to_update_dict(obj_in))
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete_idea_access(self, id: UUID) -> Optional[IdeaAccess]:
        db_obj = await self.get_idea_access(id=id)
        if not db_obj:
            return None

        await self.db.delete(db_obj)
        await self.db.commit()
        return db_obj


async def get_idea_access_service(db: AsyncSession = Depends(get_async_db)) -> IdeaAccessService:
    return IdeaAccessService(db)

# Legacy aliases
async def check_idea_access(db: AsyncSession, idea_id: UUID, user_id: UUID, required_perm: str = "view") -> bool:
    """Legacy async alias for checking idea access."""
    return await IdeaAccessService(db).check_idea_access(idea_id, user_id, required_perm)

async def grant_access(db: AsyncSession, idea_id: UUID, user_id: UUID, permissions: Dict[str, bool]) -> IdeaAccess:
    """Legacy async alias for granting idea access."""
    return await IdeaAccessService(db).grant_access(idea_id, user_id, permissions)
