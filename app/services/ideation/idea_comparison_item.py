from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

<<<<<<< HEAD
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ComparisonItem
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict
from app.repositories.idea_repository import ComparisonItemRepository
=======
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_async_db
from app.models import ComparisonItem
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict, _apply_updates
>>>>>>> origin/main

logger = logging.getLogger(__name__)


class ComparisonItemService(BaseService):
    """Service for managing items within an Idea Comparison."""
    db: AsyncSession

<<<<<<< HEAD
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self.repo = ComparisonItemRepository(db)

    async def get_comparison_item(self, id: UUID) -> Optional[ComparisonItem]:
        """Retrieve a single comparison item by ID."""
        return await self.repo.get(id)

    async def get_comparison_items(self, skip: int = 0, limit: int = 100) -> List[ComparisonItem]:
        """Retrieve pagination comparison items."""
        return await self.repo.get_all(skip=skip, limit=limit)

    async def create_comparison_item(self, obj_in: Any) -> ComparisonItem:
        """Create a new comparison item record.
        
        Uses create_safe() to handle concurrent requests attempting to create
        the same comparison item (uniqueness constraint on comparison_id, idea_id).
        If the item already exists, it will be updated with the new data.
        """
        data = _to_update_dict(obj_in)
        comparison_id = data.get("comparison_id")
        idea_id = data.get("idea_id")
        
        if comparison_id is not None and idea_id is not None:
            # First try with a safe create that handles IntegrityError gracefully
            created = await self.repo.create_safe(data, auto_commit=True)
            if created is not None:
                return created
            
            # If create_safe returned None, another transaction inserted this item.
            # Fetch it and update with the provided data.
            existing = await self.repo.get_by_comparison_and_idea(comparison_id, idea_id)
            if existing is not None:
                return await self.repo.update(existing, data)
        
        # Fallback: create without uniqueness check (shouldn't reach here normally)
        return await self.repo.create(data)

    async def update_comparison_item(self, db_obj: ComparisonItem, obj_in: Any) -> ComparisonItem:
        """Apply partial updates to a comparison item."""
        return await self.repo.update(db_obj, _to_update_dict(obj_in))

    async def delete_comparison_item(self, id: UUID) -> Optional[ComparisonItem]:
        """Delete a comparison item by ID."""
        return await self.repo.delete(id)

    async def add_item_to_comparison(self, comp_id: UUID, idea_id: UUID) -> ComparisonItem:
        """Add an idea to a comparison, automatically calculating the next rank index.
        
        Uses create_safe() to handle concurrent requests attempting to add the same
        idea to the comparison (uniqueness constraint on comparison_id, idea_id).
        """
        existing = await self.repo.get_by_comparison_and_idea(comp_id, idea_id)
        if existing is not None:
            return existing
        
        last_rank = await self.repo.get_last_rank(comp_id)
        next_rank = 0 if last_rank is None else (last_rank.rank_index + 1)
        
        # Use create_safe to handle race conditions
        created = await self.repo.create_safe(
            {"comparison_id": comp_id, "idea_id": idea_id, "rank_index": next_rank},
            auto_commit=True
        )
        if created is not None:
            return created
        
        # If create_safe returned None, another transaction inserted this item.
        # Fetch and return it.
        existing = await self.repo.get_by_comparison_and_idea(comp_id, idea_id)
        if existing is not None:
            return existing
        
        # This should not happen in practice. Raise an error.
        raise RuntimeError(
            f"Failed to add idea {idea_id} to comparison {comp_id}"
        )


async def get_comparison_item_service(
    db: AsyncSession,
) -> ComparisonItemService:
=======
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
>>>>>>> origin/main
    """Dependency provider for ComparisonItemService."""
    return ComparisonItemService(db)


<<<<<<< HEAD

=======
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
>>>>>>> origin/main
