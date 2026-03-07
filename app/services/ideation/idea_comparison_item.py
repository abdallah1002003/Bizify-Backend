from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_async_db
from app.models import ComparisonItem
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict, _apply_updates

logger = logging.getLogger(__name__)


class ComparisonItemService(BaseService):
    """Service for managing items within an Idea Comparison."""
    db: AsyncSession

    async def get_comparison_item(self, id: UUID) -> Optional[ComparisonItem]:
        """Retrieve a single comparison item by ID."""
        stmt = select(ComparisonItem).where(ComparisonItem.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_comparison_items(self, skip: int = 0, limit: int = 100) -> List[ComparisonItem]:
        """Retrieve pagination comparison items."""
        stmt = select(ComparisonItem).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

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
        stmt = (
            select(ComparisonItem)
            .where(ComparisonItem.comparison_id == comp_id)
            .order_by(ComparisonItem.rank_index.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        last_rank = result.scalar_one_or_none()
        
        next_rank = 0 if last_rank is None else (last_rank.rank_index + 1)
        return await self.create_comparison_item(
            {"comparison_id": comp_id, "idea_id": idea_id, "rank_index": next_rank},
        )


async def get_comparison_item_service(db: AsyncSession = Depends(get_async_db)) -> ComparisonItemService:
    """Dependency provider for ComparisonItemService."""
    return ComparisonItemService(db)


# ----------------------------
# Legacy Aliases
# ----------------------------

async def get_comparison_item(db: AsyncSession, id: UUID) -> Optional[ComparisonItem]:
    return await ComparisonItemService(db).get_comparison_item(id)


async def get_comparison_items(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[ComparisonItem]:
    return await ComparisonItemService(db).get_comparison_items(skip, limit)


async def create_comparison_item(db: AsyncSession, obj_in: Any) -> ComparisonItem:
    return await ComparisonItemService(db).create_comparison_item(obj_in)


async def update_comparison_item(db: AsyncSession, db_obj: ComparisonItem, obj_in: Any) -> ComparisonItem:
    return await ComparisonItemService(db).update_comparison_item(db_obj, obj_in)


async def delete_comparison_item(db: AsyncSession, id: UUID) -> Optional[ComparisonItem]:
    return await ComparisonItemService(db).delete_comparison_item(id)


async def add_item_to_comparison(db: AsyncSession, comp_id: UUID, idea_id: UUID) -> ComparisonItem:
    return await ComparisonItemService(db).add_item_to_comparison(comp_id, idea_id)
