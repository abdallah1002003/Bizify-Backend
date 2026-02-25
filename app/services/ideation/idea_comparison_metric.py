# ruff: noqa
"""
Idea Comparison Metric CRUD operations.
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import ComparisonMetric

logger = logging.getLogger(__name__)

from app.core.crud_utils import _to_update_dict, _apply_updates

# ----------------------------
# ComparisonMetric CRUD
# ----------------------------

def get_comparison_metric(db: Session, id: UUID) -> Optional[ComparisonMetric]:
    return db.query(ComparisonMetric).filter(ComparisonMetric.id == id).first()  # type: ignore[no-any-return]


def get_comparison_metrics(db: Session, skip: int = 0, limit: int = 100) -> List[ComparisonMetric]:
    return db.query(ComparisonMetric).offset(skip).limit(limit).all()  # type: ignore[no-any-return]


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
