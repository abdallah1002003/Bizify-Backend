from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_db
from app.models import ComparisonItem
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict, _apply_updates

logger = logging.getLogger(__name__)


class ComparisonItemService(BaseService):
    """Service for managing items within an Idea Comparison."""
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        from app.repositories.idea_repository import ComparisonItemRepository
        self.repo = ComparisonItemRepository(db)

    async def get_comparison_item(self, id: UUID) -> Optional[ComparisonItem]:
        """Retrieve a single comparison item by ID."""
        return await self.repo.get(id)

    async def get_comparison_items(self, skip: int = 0, limit: int = 100) -> List[ComparisonItem]:
        """Retrieve pagination comparison items."""
        return await self.repo.get_multi(skip=skip, limit=limit)

    async def create_comparison_item(self, obj_in: Any) -> ComparisonItem:
        """Create a new comparison item record."""
        db_obj = ComparisonItem(**_to_update_dict(obj_in))
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update_comparison_item(self, db_obj: ComparisonItem, obj_in: Any) -> ComparisonItem:
        """Apply partial updates to a comparison item."""
        _apply_updates(db_obj, _to_update_dict(obj_in))
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete_comparison_item(self, id: UUID) -> Optional[ComparisonItem]:
        """Delete a comparison item by ID."""
        db_obj = await self.get_comparison_item(id=id)
        if not db_obj:
            return None

        await self.db.delete(db_obj)
        await self.db.commit()
        return db_obj

    async def add_item_to_comparison(self, comp_id: UUID, idea_id: UUID) -> ComparisonItem:
        """Add an idea to a comparison, automatically calculating the next rank index."""
        # Check existing first
        existing = await self.repo.get_by_comparison_and_idea(comp_id, idea_id)
        if existing:
            return existing

        last_rank_obj = await self.repo.get_last_rank(comp_id)
        next_rank = 0 if last_rank_obj is None else (last_rank_obj.rank_index + 1)
        
        data = {"comparison_id": comp_id, "idea_id": idea_id, "rank_index": next_rank}
        created = await self.repo.create_safe(data)
        if created:
            return created
        
        # Concurrency fallback
        existing_again = await self.repo.get_by_comparison_and_idea(comp_id, idea_id)
        if existing_again:
            return existing_again
            
        return await self.repo.create(data)


async def get_comparison_item_service(db: AsyncSession = Depends(get_async_db)) -> ComparisonItemService:
    """Dependency provider for ComparisonItemService."""
    return ComparisonItemService(db)


# ----------------------------
# Legacy Aliases
# ----------------------------

async def get_comparison_item(db: AsyncSession, comp_id: UUID, idea_id: UUID) -> Optional[ComparisonItem]:
    return await ComparisonItemService(db).add_item_to_comparison(comp_id, idea_id)
