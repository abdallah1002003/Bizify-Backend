"""Shared CRUD helpers for billing service modules."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypeVar, cast
from uuid import UUID

from sqlalchemy.orm import Session

ModelT = TypeVar("ModelT")


def get_by_id(db: Session, model: Any, id: UUID) -> Optional[ModelT]:
    """Fetch a single record by `id` for a SQLAlchemy model."""

    return cast(Optional[ModelT], db.query(model).filter(model.id == id).first())


def list_records(
    db: Session,
    model: Any,
    skip: int = 0,
    limit: int = 100,
    filters: Optional[Dict[str, Any]] = None,
) -> List[ModelT]:
    """Fetch records with optional equality filters and pagination."""

    query = db.query(model)
    if filters:
        for field_name, value in filters.items():
            if value is None:
                continue
            query = query.filter(getattr(model, field_name) == value)
    return cast(List[ModelT], query.offset(skip).limit(limit).all())

