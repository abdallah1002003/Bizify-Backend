from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_async_db
from app.models import ComparisonMetric
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict, _apply_updates

logger = logging.getLogger(__name__)


class ComparisonMetricService(BaseService):
    """Service for managing metrics within an Idea Comparison."""
    db: AsyncSession

    async def get_comparison_metric(self, id: UUID) -> Optional[ComparisonMetric]:
        """Retrieve a single comparison metric record by ID."""
        stmt = select(ComparisonMetric).where(ComparisonMetric.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_comparison_metrics(self, skip: int = 0, limit: int = 100) -> List[ComparisonMetric]:
        """Retrieve pagination comparison metrics."""
        stmt = select(ComparisonMetric).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_comparison_metric(self, obj_in: Any) -> ComparisonMetric:
        """Create a new comparison metric record."""
        db_obj = ComparisonMetric(**_to_update_dict(obj_in))
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update_comparison_metric(self, db_obj: ComparisonMetric, obj_in: Any) -> ComparisonMetric:
        """Apply partial updates to a comparison metric."""
        _apply_updates(db_obj, _to_update_dict(obj_in))
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete_comparison_metric(self, id: UUID) -> Optional[ComparisonMetric]:
        """Delete a comparison metric record by ID."""
        db_obj = await self.get_comparison_metric(id=id)
        if not db_obj:
            return None

        await self.db.delete(db_obj)
        await self.db.commit()
        return db_obj


async def get_comparison_metric_service(db: AsyncSession = Depends(get_async_db)) -> ComparisonMetricService:
    """Dependency provider for ComparisonMetricService."""
    return ComparisonMetricService(db)


# ----------------------------
# Legacy Aliases
# ----------------------------

async def get_comparison_metric(db: AsyncSession, id: UUID) -> Optional[ComparisonMetric]:
    return await ComparisonMetricService(db).get_comparison_metric(id)


async def get_comparison_metrics(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[ComparisonMetric]:
    return await ComparisonMetricService(db).get_comparison_metrics(skip, limit)


async def create_comparison_metric(db: AsyncSession, obj_in: Any) -> ComparisonMetric:
    return await ComparisonMetricService(db).create_comparison_metric(obj_in)


async def update_comparison_metric(db: AsyncSession, db_obj: ComparisonMetric, obj_in: Any) -> ComparisonMetric:
    return await ComparisonMetricService(db).update_comparison_metric(db_obj, obj_in)


async def delete_comparison_metric(db: AsyncSession, id: UUID) -> Optional[ComparisonMetric]:
    return await ComparisonMetricService(db).delete_comparison_metric(id)
