"""
Idea Experiment CRUD operations.
"""
from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Experiment, Idea
from app.models.enums import IdeaStatus
from app.services.ideation import idea_service

logger = logging.getLogger(__name__)

from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates

# ----------------------------
# Experiment CRUD
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
    if not idea_service.check_idea_access(db, idea_id, creator_id, "experiment"):
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
