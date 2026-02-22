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

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_update_dict(obj_in: Any) -> Dict[str, Any]:
    if obj_in is None:
        return {}
    if hasattr(obj_in, "model_dump"):
        return obj_in.model_dump(exclude_unset=True)
    return dict(obj_in)


def _apply_updates(db_obj: Any, update_data: Dict[str, Any]) -> Any:
    for field, value in update_data.items():
        if hasattr(db_obj, field):
            setattr(db_obj, field, value)
    return db_obj


# ----------------------------
# IdeaMetric CRUD
# ----------------------------

def get_idea_metric(db: Session, id: UUID) -> Optional[IdeaMetric]:
    return db.query(IdeaMetric).filter(IdeaMetric.id == id).first()


def get_idea_metrics(
    db: Session,
    idea_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[IdeaMetric]:
    query = db.query(IdeaMetric)
    if idea_id is not None:
        query = query.filter(IdeaMetric.idea_id == idea_id)
    return query.offset(skip).limit(limit).all()


def create_idea_metric(db: Session, obj_in: Any) -> IdeaMetric:
    db_obj = IdeaMetric(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)

    if db_obj.type == "AI_ANALYSIS":
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

    db.delete(db_obj)
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
        .filter(IdeaMetric.idea_id == idea_id, IdeaMetric.name == metric_name)
        .order_by(IdeaMetric.recorded_at.desc())
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
