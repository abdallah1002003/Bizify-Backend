from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import IdeaComparison
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict
from app.repositories.idea_repository import IdeaComparisonRepository

logger = logging.getLogger(__name__)


class IdeaComparisonService(BaseService):
    """Service for managing Idea Comparisons."""
    db: AsyncSession

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
    """Dependency provider for IdeaComparisonService."""
    return IdeaComparisonService(db)


