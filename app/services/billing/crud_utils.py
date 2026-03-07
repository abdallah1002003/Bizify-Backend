from __future__ import annotations

from typing import Any, Dict, List, Optional, TypeVar, cast
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

ModelT = TypeVar("ModelT")


async def get_by_id(db: AsyncSession, model: Any, id: UUID) -> Optional[ModelT]:
    """Fetch a single record by `id` for a SQLAlchemy model."""
    return await db.get(model, id)


async def list_records(
    db: AsyncSession,
    model: Any,
    skip: int = 0,
    limit: int = 100,
    filters: Optional[Dict[str, Any]] = None,
) -> List[ModelT]:
    """Fetch records with optional equality filters and pagination."""
    stmt = select(model)
    if filters:
        for field_name, value in filters.items():
            if value is None:
                continue
            stmt = stmt.where(getattr(model, field_name) == value)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return cast(List[ModelT], list(result.scalars().all()))

