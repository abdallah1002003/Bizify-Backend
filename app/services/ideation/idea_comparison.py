from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

<<<<<<< HEAD
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import IdeaComparison
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict
from app.repositories.idea_repository import IdeaComparisonRepository
=======
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_async_db
from app.models import IdeaComparison
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict, _apply_updates
>>>>>>> origin/main

logger = logging.getLogger(__name__)


class IdeaComparisonService(BaseService):
    """Service for managing Idea Comparisons."""
    db: AsyncSession

<<<<<<< HEAD
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self.repo = IdeaComparisonRepository(db)

    async def get_idea_comparison(self, id: UUID) -> Optional[IdeaComparison]:
        """Retrieve a single comparison record by ID."""
        return await self.repo.get(id)

    async def get_idea_comparisons(self, skip: int = 0, limit: int = 100) -> List[IdeaComparison]:
        """Retrieve pagination comparison records."""
        return await self.repo.get_all(skip=skip, limit=limit)

    async def create_idea_comparison(self, obj_in: Any) -> IdeaComparison:
        """Create a new idea comparison."""
        return await self.repo.create(_to_update_dict(obj_in))

    async def update_idea_comparison(self, db_obj: IdeaComparison, obj_in: Any) -> IdeaComparison:
        """Apply partial updates to a comparison record."""
        return await self.repo.update(db_obj, _to_update_dict(obj_in))

    async def delete_idea_comparison(self, id: UUID) -> Optional[IdeaComparison]:
        """Delete a comparison record."""
        return await self.repo.delete(id)

    async def create_comparison(self, title: str, user_id: UUID) -> IdeaComparison:
        """Helper to create a comparison with a specific name/title."""
        return await self.repo.create({"name": title, "user_id": user_id})


async def get_idea_comparison_service(db: AsyncSession) -> IdeaComparisonService:
=======
    async def get_idea_comparison(self, id: UUID) -> Optional[IdeaComparison]:
        """Retrieve a single comparison record by ID."""
        stmt = select(IdeaComparison).where(IdeaComparison.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_idea_comparisons(self, skip: int = 0, limit: int = 100) -> List[IdeaComparison]:
        """Retrieve pagination comparison records."""
        stmt = select(IdeaComparison).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

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
        return await self.create_idea_comparison({"name": title, "user_id": user_id})


async def get_idea_comparison_service(db: AsyncSession = Depends(get_async_db)) -> IdeaComparisonService:
>>>>>>> origin/main
    """Dependency provider for IdeaComparisonService."""
    return IdeaComparisonService(db)


<<<<<<< HEAD
=======
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
>>>>>>> origin/main
