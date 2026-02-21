from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import (
    ComparisonItem,
    ComparisonMetric,
    Experiment,
    Idea,
    IdeaAccess,
    IdeaComparison,
    IdeaMetric,
    IdeaVersion,
)
from app.models.enums import IdeaStatus

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


def _create_snapshot(db: Session, idea: Idea, created_by: Optional[UUID] = None) -> IdeaVersion:
    snapshot = {
        "title": idea.title,
        "description": idea.description,
        "status": idea.status.value if hasattr(idea.status, "value") else str(idea.status),
        "ai_score": idea.ai_score,
        "is_archived": idea.is_archived,
    }
    db_obj = IdeaVersion(
        idea_id=idea.id,
        created_by=created_by or idea.owner_id,
        snapshot_json=snapshot,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


# ----------------------------
# Idea
# ----------------------------

def get_idea(db: Session, id: UUID, user_id: Optional[UUID] = None) -> Optional[Idea]:
    db_obj = db.query(Idea).filter(Idea.id == id).first()
    if db_obj is None:
        return None

    if user_id is not None and not check_idea_access(db, id, user_id, "view"):
        return None

    return db_obj


def get_ideas(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
) -> List[Idea]:
    query = db.query(Idea)
    if user_id is not None:
        query = query.outerjoin(IdeaAccess).filter(
            (Idea.owner_id == user_id) | (IdeaAccess.user_id == user_id)
        )
    return query.distinct().offset(skip).limit(limit).all()


def create_idea(db: Session, obj_in: Any) -> Idea:
    db_obj = Idea(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)

    _create_snapshot(db, db_obj)
    return db_obj


def update_idea(db: Session, db_obj: Idea, obj_in: Any, performer_id: Optional[UUID] = None) -> Idea:
    if performer_id is not None and not check_idea_access(db, db_obj.id, performer_id, "edit"):
        raise PermissionError("Not authorized to edit this idea")

    update_data = _to_update_dict(obj_in)
    major_changed = any(field in update_data for field in ("title", "description", "status"))

    _apply_updates(db_obj, update_data)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)

    if major_changed:
        _create_snapshot(db, db_obj, created_by=performer_id)

    return db_obj


def delete_idea(db: Session, id: UUID) -> Optional[Idea]:
    db_obj = db.query(Idea).filter(Idea.id == id).first()
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


# ----------------------------
# Access control
# ----------------------------

def check_idea_access(db: Session, idea_id: UUID, user_id: UUID, required_perm: str = "view") -> bool:
    idea = db.query(Idea).filter(Idea.id == idea_id).first()
    if idea is None:
        return False

    if idea.owner_id == user_id:
        return True

    access = (
        db.query(IdeaAccess)
        .filter(IdeaAccess.idea_id == idea_id, IdeaAccess.user_id == user_id)
        .first()
    )
    if access is None:
        return False

    if required_perm == "view":
        return True
    if required_perm == "edit":
        return bool(access.can_edit)
    if required_perm == "delete":
        return bool(access.can_delete)
    if required_perm == "experiment":
        return bool(access.can_experiment)

    return False


def grant_access(db: Session, idea_id: UUID, user_id: UUID, permissions: Dict[str, bool]) -> IdeaAccess:
    access = (
        db.query(IdeaAccess)
        .filter(IdeaAccess.idea_id == idea_id, IdeaAccess.user_id == user_id)
        .first()
    )
    if access is None:
        access = IdeaAccess(
            idea_id=idea_id,
            user_id=user_id,
            can_edit=permissions.get("edit", False),
            can_delete=permissions.get("delete", False),
            can_experiment=permissions.get("experiment", False),
        )
        db.add(access)
    else:
        access.can_edit = permissions.get("edit", access.can_edit)
        access.can_delete = permissions.get("delete", access.can_delete)
        access.can_experiment = permissions.get("experiment", access.can_experiment)

    db.commit()
    db.refresh(access)
    return access


# ----------------------------
# IdeaVersion
# ----------------------------

def get_idea_version(db: Session, id: UUID) -> Optional[IdeaVersion]:
    return db.query(IdeaVersion).filter(IdeaVersion.id == id).first()


def get_idea_versions(
    db: Session,
    idea_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[IdeaVersion]:
    query = db.query(IdeaVersion)
    if idea_id is not None:
        query = query.filter(IdeaVersion.idea_id == idea_id)
    return query.order_by(IdeaVersion.created_at.desc()).offset(skip).limit(limit).all()


def create_idea_version(db: Session, obj_in: Any) -> IdeaVersion:
    db_obj = IdeaVersion(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_idea_version(db: Session, db_obj: IdeaVersion, obj_in: Any) -> IdeaVersion:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_idea_version(db: Session, id: UUID) -> Optional[IdeaVersion]:
    db_obj = get_idea_version(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


# ----------------------------
# IdeaMetric
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


# ----------------------------
# Experiment
# ----------------------------

def get_experiment(db: Session, id: UUID) -> Optional[Experiment]:
    return db.query(Experiment).filter(Experiment.id == id).first()


def get_experiments(
    db: Session,
    idea_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Experiment]:
    query = db.query(Experiment)
    if idea_id is not None:
        query = query.filter(Experiment.idea_id == idea_id)
    return query.offset(skip).limit(limit).all()


def create_experiment(db: Session, obj_in: Any) -> Experiment:
    db_obj = Experiment(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_experiment(db: Session, db_obj: Experiment, obj_in: Any) -> Experiment:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_experiment(db: Session, id: UUID) -> Optional[Experiment]:
    db_obj = get_experiment(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


def initiate_experiment(db: Session, idea_id: UUID, hypothesis: str, creator_id: UUID) -> Experiment:
    if not check_idea_access(db, idea_id, creator_id, "experiment"):
        raise PermissionError("Not authorized to experiment on this idea")

    return create_experiment(
        db,
        {
            "idea_id": idea_id,
            "created_by": creator_id,
            "hypothesis": hypothesis,
            "status": "ACTIVE",
            "result_summary": "",
        },
    )


def finalize_experiment(db: Session, exp_id: UUID, result_json: dict, status: str) -> Optional[Experiment]:
    db_obj = get_experiment(db, id=exp_id)
    if not db_obj:
        return None

    db_obj.status = status
    db_obj.result_summary = str(result_json)
    db.commit()
    db.refresh(db_obj)

    if status == "SUCCESSFUL":
        idea = db.query(Idea).filter(Idea.id == db_obj.idea_id).first()
        if idea is not None:
            idea.status = IdeaStatus.VALIDATED
            db.commit()

    return db_obj


# ----------------------------
# IdeaAccess
# ----------------------------

def get_idea_access(db: Session, id: UUID) -> Optional[IdeaAccess]:
    return db.query(IdeaAccess).filter(IdeaAccess.id == id).first()


def get_idea_accesss(db: Session, skip: int = 0, limit: int = 100) -> List[IdeaAccess]:
    return db.query(IdeaAccess).offset(skip).limit(limit).all()


def create_idea_access(db: Session, obj_in: Any) -> IdeaAccess:
    db_obj = IdeaAccess(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_idea_access(db: Session, db_obj: IdeaAccess, obj_in: Any) -> IdeaAccess:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_idea_access(db: Session, id: UUID) -> Optional[IdeaAccess]:
    db_obj = get_idea_access(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


# ----------------------------
# IdeaComparison
# ----------------------------

def get_idea_comparison(db: Session, id: UUID) -> Optional[IdeaComparison]:
    return db.query(IdeaComparison).filter(IdeaComparison.id == id).first()


def get_idea_comparisons(db: Session, skip: int = 0, limit: int = 100) -> List[IdeaComparison]:
    return db.query(IdeaComparison).offset(skip).limit(limit).all()


def create_idea_comparison(db: Session, obj_in: Any) -> IdeaComparison:
    db_obj = IdeaComparison(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_idea_comparison(db: Session, db_obj: IdeaComparison, obj_in: Any) -> IdeaComparison:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_idea_comparison(db: Session, id: UUID) -> Optional[IdeaComparison]:
    db_obj = get_idea_comparison(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


def create_comparison(db: Session, title: str, user_id: UUID) -> IdeaComparison:
    return create_idea_comparison(db, {"name": title, "user_id": user_id})


# ----------------------------
# ComparisonItem
# ----------------------------

def get_comparison_item(db: Session, id: UUID) -> Optional[ComparisonItem]:
    return db.query(ComparisonItem).filter(ComparisonItem.id == id).first()


def get_comparison_items(db: Session, skip: int = 0, limit: int = 100) -> List[ComparisonItem]:
    return db.query(ComparisonItem).offset(skip).limit(limit).all()


def create_comparison_item(db: Session, obj_in: Any) -> ComparisonItem:
    db_obj = ComparisonItem(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_comparison_item(db: Session, db_obj: ComparisonItem, obj_in: Any) -> ComparisonItem:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_comparison_item(db: Session, id: UUID) -> Optional[ComparisonItem]:
    db_obj = get_comparison_item(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


def add_item_to_comparison(db: Session, comp_id: UUID, idea_id: UUID) -> ComparisonItem:
    # Append at the end.
    last_rank = (
        db.query(ComparisonItem)
        .filter(ComparisonItem.comparison_id == comp_id)
        .order_by(ComparisonItem.rank_index.desc())
        .first()
    )
    next_rank = 0 if last_rank is None else (last_rank.rank_index + 1)
    return create_comparison_item(
        db,
        {"comparison_id": comp_id, "idea_id": idea_id, "rank_index": next_rank},
    )


# ----------------------------
# ComparisonMetric
# ----------------------------

def get_comparison_metric(db: Session, id: UUID) -> Optional[ComparisonMetric]:
    return db.query(ComparisonMetric).filter(ComparisonMetric.id == id).first()


def get_comparison_metrics(db: Session, skip: int = 0, limit: int = 100) -> List[ComparisonMetric]:
    return db.query(ComparisonMetric).offset(skip).limit(limit).all()


def create_comparison_metric(db: Session, obj_in: Any) -> ComparisonMetric:
    db_obj = ComparisonMetric(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_comparison_metric(db: Session, db_obj: ComparisonMetric, obj_in: Any) -> ComparisonMetric:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_comparison_metric(db: Session, id: UUID) -> Optional[ComparisonMetric]:
    db_obj = get_comparison_metric(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


def get_detailed_status() -> Dict[str, Any]:
    return {
        "module": "idea_service",
        "status": "operational",
        "timestamp": _utc_now().isoformat(),
    }


def reset_internal_state() -> None:
    logger.info("idea_service reset_internal_state called")
