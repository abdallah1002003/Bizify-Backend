"""
Business Roadmap and Roadmap Stage operations.
"""
from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import BusinessRoadmap, RoadmapStage
from app.models.enums import RoadmapStageStatus, StageType

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


def _recalculate_roadmap_completion(db: Session, roadmap_id: UUID) -> None:
    stages = db.query(RoadmapStage).filter(RoadmapStage.roadmap_id == roadmap_id).all()
    if not stages:
        return

    completed = sum(1 for stage in stages if stage.status == RoadmapStageStatus.COMPLETED)
    completion = (completed / len(stages)) * 100.0

    roadmap = db.query(BusinessRoadmap).filter(BusinessRoadmap.id == roadmap_id).first()
    if roadmap is None:
        return

    roadmap.completion_percentage = completion
    db.commit()


# ----------------------------
# BusinessRoadmap
# ----------------------------

def get_roadmap(db: Session, business_id: UUID) -> Optional[BusinessRoadmap]:
    return db.query(BusinessRoadmap).filter(BusinessRoadmap.business_id == business_id).first()


def get_business_roadmap(db: Session, id: UUID) -> Optional[BusinessRoadmap]:
    return db.query(BusinessRoadmap).filter(BusinessRoadmap.id == id).first()


def get_business_roadmaps(db: Session, skip: int = 0, limit: int = 100) -> List[BusinessRoadmap]:
    return db.query(BusinessRoadmap).offset(skip).limit(limit).all()


def init_default_roadmap(db: Session, business_id: UUID) -> BusinessRoadmap:
    existing = get_roadmap(db, business_id=business_id)
    if existing is not None:
        return existing

    db_obj = BusinessRoadmap(business_id=business_id, completion_percentage=0.0)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)

    # Default first stage.
    add_roadmap_stage(db, db_obj.id, StageType.READINESS, 0)
    return db_obj


def create_business_roadmap(db: Session, obj_in: Any) -> BusinessRoadmap:
    db_obj = BusinessRoadmap(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_business_roadmap(db: Session, db_obj: BusinessRoadmap, obj_in: Any) -> BusinessRoadmap:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_business_roadmap(db: Session, id: UUID) -> Optional[BusinessRoadmap]:
    db_obj = get_business_roadmap(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


# ----------------------------
# RoadmapStage
# ----------------------------

def get_roadmap_stage(db: Session, id: UUID) -> Optional[RoadmapStage]:
    return db.query(RoadmapStage).filter(RoadmapStage.id == id).first()


def get_roadmap_stages(
    db: Session,
    roadmap_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[RoadmapStage]:
    query = db.query(RoadmapStage)
    if roadmap_id is not None:
        query = query.filter(RoadmapStage.roadmap_id == roadmap_id)
    return query.order_by(RoadmapStage.order_index.asc()).offset(skip).limit(limit).all()


def add_roadmap_stage(db: Session, roadmap_id: UUID, stage_type: StageType, order_index: int) -> RoadmapStage:
    db_stage = RoadmapStage(
        roadmap_id=roadmap_id,
        stage_type=stage_type,
        order_index=order_index,
        status=RoadmapStageStatus.PLANNED,
    )
    db.add(db_stage)
    db.commit()
    db.refresh(db_stage)
    return db_stage


def create_roadmap_stage(db: Session, obj_in: Any) -> RoadmapStage:
    db_obj = RoadmapStage(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_roadmap_stage(db: Session, db_obj: RoadmapStage, obj_in: Any) -> RoadmapStage:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)

    if db_obj.status == RoadmapStageStatus.COMPLETED:
        _recalculate_roadmap_completion(db, db_obj.roadmap_id)

    return db_obj


def delete_roadmap_stage(db: Session, id: UUID) -> Optional[RoadmapStage]:
    db_obj = get_roadmap_stage(db, id=id)
    if not db_obj:
        return None

    roadmap_id = db_obj.roadmap_id
    db.delete(db_obj)
    db.commit()
    _recalculate_roadmap_completion(db, roadmap_id)
    return db_obj


def transition_stage(db: Session, stage_id: UUID, new_status: RoadmapStageStatus) -> Optional[RoadmapStage]:
    db_stage = get_roadmap_stage(db, id=stage_id)
    if db_stage is None:
        return None

    if new_status == RoadmapStageStatus.ACTIVE and db_stage.order_index > 0:
        prev_stage = (
            db.query(RoadmapStage)
            .filter(
                RoadmapStage.roadmap_id == db_stage.roadmap_id,
                RoadmapStage.order_index == db_stage.order_index - 1,
            )
            .first()
        )
        if prev_stage and prev_stage.status != RoadmapStageStatus.COMPLETED:
            raise ValueError("Prerequisite stage not completed")

    db_stage.status = new_status
    if new_status == RoadmapStageStatus.COMPLETED:
        db_stage.completed_at = _utc_now()

    db.commit()
    db.refresh(db_stage)

    if new_status == RoadmapStageStatus.COMPLETED:
        _recalculate_roadmap_completion(db, db_stage.roadmap_id)

    return db_stage


def update_stage_status(db: Session, stage_id: UUID, new_status: RoadmapStageStatus) -> Optional[RoadmapStage]:
    """Backward-compatible alias used by older tests/services."""
    return transition_stage(db, stage_id=stage_id, new_status=new_status)
