
from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ComparisonMetric
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict
from app.repositories.idea_repository import ComparisonMetricRepository

logger = logging.getLogger(__name__)


class ComparisonMetricService(BaseService):
    """Service for managing metrics within an Idea Comparison."""
    db: AsyncSession

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
    """Dependency provider for ComparisonMetricService."""
    return ComparisonMetricService(db)


