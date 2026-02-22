"""
Idea Comparison Item CRUD operations.
"""
from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import ComparisonItem

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
# ComparisonItem CRUD
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
