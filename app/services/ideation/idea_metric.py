"""
Idea Metric CRUD operations and analytics.
"""
from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Idea, IdeaMetric
from app.models.enums import MetricType

logger = logging.getLogger(__name__)

from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates

# ----------------------------
# IdeaMetric CRUD
# ----------------------------

def get_idea_metric(db: Session, id: UUID) -> Optional[IdeaMetric]:
    return db.query(IdeaMetric).filter(IdeaMetric.id == id, IdeaMetric.is_deleted == False).first()


def get_idea_metrics(
    db: Session,
    idea_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[IdeaMetric]:
    query = db.query(IdeaMetric).filter(IdeaMetric.is_deleted == False)
    if idea_id is not None:
        query = query.filter(IdeaMetric.idea_id == idea_id)
    return query.offset(skip).limit(limit).all()


def create_idea_metric(db: Session, obj_in: Any) -> IdeaMetric:
    db_obj = IdeaMetric(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)

    # Check if the metric type is AI_ANALYSIS and update idea's AI score
    if db_obj.type == MetricType.AI_ANALYSIS or db_obj.type == "AI_ANALYSIS":
        idea = db.query(Idea).filter(Idea.id == db_obj.idea_id).first()
        if idea is not None:
            idea.ai_score = db_obj.value
            db.commit()

    return db_obj


def update_idea_metric(db: Session, db_obj: IdeaMetric, obj_in: Any) -> IdeaMetric:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_idea_metric(db: Session, id: UUID) -> Optional[IdeaMetric]:
    db_obj = get_idea_metric(db, id=id)
    if not db_obj:
        return None

    db_obj.is_deleted = True
    db_obj.deleted_at = _utc_now()
    db.commit()
    return db_obj


def record_metric(db: Session, idea_id: UUID, name: str, value: float, category: str, creator_id: UUID) -> IdeaMetric:
    return create_idea_metric(
        db,
        {
            "idea_id": idea_id,
            "created_by": creator_id,
            "name": name,
            "value": value,
            "type": category,
        },
    )


def get_metric_trends(db: Session, idea_id: UUID, metric_name: str) -> Dict[str, Any]:
    metrics = (
        db.query(IdeaMetric)
        .filter(IdeaMetric.idea_id == idea_id, IdeaMetric.name == metric_name, IdeaMetric.is_deleted == False)
        .order_by(IdeaMetric.created_at.desc())
        .limit(2)
        .all()
    )
    if not metrics:
        return {"current": 0, "trend": "stable", "delta": 0}
    if len(metrics) == 1:
        return {"current": metrics[0].value, "trend": "stable", "delta": 0}

    delta = metrics[0].value - metrics[1].value
    trend = "improving" if delta > 0 else "declining" if delta < 0 else "stable"
    return {"current": metrics[0].value, "trend": trend, "delta": delta}
