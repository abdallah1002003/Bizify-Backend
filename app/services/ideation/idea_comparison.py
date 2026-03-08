from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_db
from app.models import IdeaComparison
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict, _apply_updates

logger = logging.getLogger(__name__)


class IdeaComparisonService(BaseService):
    """Service for managing Idea Comparisons."""
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        from app.repositories.idea_repository import IdeaComparisonRepository
        self.repo = IdeaComparisonRepository(db)

    async def get_idea_comparison(self, id: UUID) -> Optional[IdeaComparison]:
        """Retrieve a single comparison record by ID."""
        return await self.repo.get(id)

    async def get_idea_comparisons(self, skip: int = 0, limit: int = 100) -> List[IdeaComparison]:
        """Retrieve pagination comparison records."""
        return await self.repo.get_multi(skip=skip, limit=limit)

    async def create_idea_comparison(self, obj_in: Any) -> IdeaComparison:
        """Create a new idea comparison."""
        db_obj = IdeaComparison(**_to_update_dict(obj_in))
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update_idea_comparison(self, db_obj: IdeaComparison, obj_in: Any) -> IdeaComparison:
        """Apply partial updates to a comparison record."""
        _apply_updates(db_obj, _to_update_dict(obj_in))
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete_idea_comparison(self, id: UUID) -> Optional[IdeaComparison]:
        """Delete a comparison record."""
        db_obj = await self.get_idea_comparison(id=id)
        if not db_obj:
            return None

        await self.db.delete(db_obj)
        await self.db.commit()
        return db_obj

    async def create_comparison(self, title: str, user_id: UUID) -> IdeaComparison:
        """Helper to create a comparison with a specific name/title."""
        return await self.repo.create({"name": title, "user_id": user_id})


async def get_idea_comparison_service(db: AsyncSession = Depends(get_async_db)) -> IdeaComparisonService:
    """Dependency provider for IdeaComparisonService."""
    return IdeaComparisonService(db)


# ----------------------------
# Legacy Aliases
# ----------------------------

async def get_idea_comparison(db: AsyncSession, id: UUID) -> Optional[IdeaComparison]:
    return await IdeaComparisonService(db).get_idea_comparison(id)


async def get_idea_comparisons(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[IdeaComparison]:
    return await IdeaComparisonService(db).get_idea_comparisons(skip, limit)


async def create_idea_comparison(db: AsyncSession, obj_in: Any) -> IdeaComparison:
    return await IdeaComparisonService(db).create_idea_comparison(obj_in)


async def update_idea_comparison(db: AsyncSession, db_obj: IdeaComparison, obj_in: Any) -> IdeaComparison:
    return await IdeaComparisonService(db).update_idea_comparison(db_obj, obj_in)


async def delete_idea_comparison(db: AsyncSession, id: UUID) -> Optional[IdeaComparison]:
    return await IdeaComparisonService(db).delete_idea_comparison(id)


async def create_comparison(db: AsyncSession, title: str, user_id: UUID) -> IdeaComparison:
    return await IdeaComparisonService(db).create_comparison(title, user_id)
