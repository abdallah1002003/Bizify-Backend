from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import IdeaMetric
from app.models.enums import MetricType
from app.services.base_service import BaseService
from app.core.crud_utils import _utc_now, _to_update_dict
from app.repositories.idea_repository import IdeaMetricRepository, IdeaRepository

logger = logging.getLogger(__name__)


class IdeaMetricService(BaseService):
    """Service for managing Idea Metrics and analytics."""
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self.repo = IdeaMetricRepository(db)
        self.idea_repo = IdeaRepository(db)

    async def get_idea_metric(self, id: UUID) -> Optional[IdeaMetric]:
        """Retrieve a single metric record by ID."""
        metric = await self.repo.get(id)
        if metric and not metric.is_deleted:
            return metric
        return None

    async def get_idea_metrics(
        self,
        idea_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[IdeaMetric]:
        """Retrieve pagination metrics with optional idea filtering."""
        if idea_id is not None:
            metrics = await self.repo.get_for_idea(idea_id)
        else:
            metrics = await self.repo.get_all()
        
        active_metrics = [m for m in metrics if not m.is_deleted]
        return active_metrics[skip:skip+limit]

    async def create_idea_metric(self, obj_in: Any) -> IdeaMetric:
        """Create a new idea metric and update idea AI score if needed."""
        db_obj = await self.repo.create(_to_update_dict(obj_in))

        if db_obj.type in (MetricType.AI_ANALYSIS, "AI_ANALYSIS"):
            idea = await self.idea_repo.get(db_obj.idea_id)
            if idea is not None:
                await self.idea_repo.update(idea, {"ai_score": db_obj.value})

        return db_obj

    async def update_idea_metric(self, db_obj: IdeaMetric, obj_in: Any) -> IdeaMetric:
        """Apply partial updates to a metric record."""
        return await self.repo.update(db_obj, _to_update_dict(obj_in))

    async def delete_idea_metric(self, id: UUID) -> Optional[IdeaMetric]:
        """Soft-delete a metric record."""
        db_obj = await self.get_idea_metric(id=id)
        if not db_obj:
            return None

        return await self.repo.update(db_obj, {
            "is_deleted": True,
            "deleted_at": _utc_now()
        })

    async def record_metric(self, idea_id: UUID, name: str, value: float, category: str, creator_id: UUID) -> IdeaMetric:
        """Record a single metric value."""
        return await self.create_idea_metric(
            {
                "idea_id": idea_id,
                "created_by": creator_id,
                "name": name,
                "value": value,
                "type": category,
            },
        )

    async def get_metric_trends(self, idea_id: UUID, metric_name: str) -> Dict[str, Any]:
        """Calculate trends between the two most recent metrics of a given name."""
        all_metrics = await self.repo.get_for_idea(idea_id)
        metrics = [m for m in all_metrics if m.name == metric_name and not m.is_deleted]
        metrics.sort(key=lambda x: x.created_at, reverse=True)
        metrics = metrics[:2]

        if not metrics:
            return {"current": 0, "trend": "stable", "delta": 0}
        if len(metrics) == 1:
            return {"current": metrics[0].value, "trend": "stable", "delta": 0}

        delta = metrics[0].value - metrics[1].value
        trend = "improving" if delta > 0 else "declining" if delta < 0 else "stable"
        return {"current": metrics[0].value, "trend": trend, "delta": delta}


async def get_idea_metric_service(db: AsyncSession) -> IdeaMetricService:
    """Dependency provider for IdeaMetricService."""
    return IdeaMetricService(db)


