<<<<<<< HEAD

=======
>>>>>>> origin/main
from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

<<<<<<< HEAD
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ComparisonMetric
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict
from app.repositories.idea_repository import ComparisonMetricRepository
=======
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_async_db
from app.models import ComparisonMetric
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict, _apply_updates
>>>>>>> origin/main

logger = logging.getLogger(__name__)


class ComparisonMetricService(BaseService):
    """Service for managing metrics within an Idea Comparison."""
    db: AsyncSession

<<<<<<< HEAD
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self.repo = ComparisonMetricRepository(db)

    async def get_comparison_metric(self, id: UUID) -> Optional[ComparisonMetric]:
        """Retrieve a single comparison metric record by ID."""
        return await self.repo.get(id)

    async def get_comparison_metrics(self, skip: int = 0, limit: int = 100) -> List[ComparisonMetric]:
        """Retrieve pagination comparison metrics."""
        return await self.repo.get_all(skip=skip, limit=limit)

    async def create_comparison_metric(self, obj_in: Any) -> ComparisonMetric:
        """Create a new comparison metric record.
        
        Uses create_safe() to handle concurrent requests attempting to create
        the same metric (uniqueness constraint on comparison_id, metric_name).
        """
        data = _to_update_dict(obj_in)
        created = await self.repo.create_safe(data, auto_commit=True)
        if created is not None:
            return created
        
        # If create_safe returned None, another transaction inserted this metric.
        # Fetch and return it.
        comparison_id = data.get("comparison_id")
        metric_name = data.get("metric_name")
        existing = await self.repo.get_by_comparison_and_metric(comparison_id, metric_name)
        if existing is not None:
            return existing
        
        # This should not happen in practice. Raise an error.
        raise RuntimeError(
            f"Failed to create comparison metric for comparison {comparison_id}, "
            f"metric {metric_name}"
        )

    async def update_comparison_metric(self, db_obj: ComparisonMetric, obj_in: Any) -> ComparisonMetric:
        """Apply partial updates to a comparison metric."""
        return await self.repo.update(db_obj, _to_update_dict(obj_in))

    async def delete_comparison_metric(self, id: UUID) -> Optional[ComparisonMetric]:
        """Delete a comparison metric record by ID."""
        return await self.repo.delete(id)


async def get_comparison_metric_service(db: AsyncSession) -> ComparisonMetricService:
=======
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
>>>>>>> origin/main
    """Dependency provider for ComparisonMetricService."""
    return ComparisonMetricService(db)


<<<<<<< HEAD
=======
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
>>>>>>> origin/main
