"""
Usage enforcement and tracking operations.
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Usage
from app.services.billing.crud_utils import get_by_id, list_records
from app.services.billing.billing_service import _to_update_dict, _apply_updates

logger = logging.getLogger(__name__)


# ----------------------------
# Usage enforcement
# ----------------------------

def check_usage_limit(db: Session, user_id: UUID, resource_type: str) -> bool:
    """Return whether the user's usage remains below the configured limit."""

    usage = (
        db.query(Usage)
        .filter(Usage.user_id == user_id, Usage.resource_type == resource_type)
        .first()
    )
    if usage is None or usage.limit_value is None:
        return True
    return usage.used < usage.limit_value


def record_usage(db: Session, user_id: UUID, resource_type: str, quantity: int = 1) -> Usage:
    """Atomically increment usage for a resource, creating the row when needed.

    Uses SELECT FOR UPDATE to prevent a race condition where two concurrent
    requests both read ``usage is None`` and both try to INSERT the same row.
    """

    usage = (
        db.query(Usage)
        .filter(Usage.user_id == user_id, Usage.resource_type == resource_type)
        .with_for_update()  # row-level lock — prevents concurrent phantom inserts
        .first()
    )
    if usage is None:
        usage = Usage(user_id=user_id, resource_type=resource_type, used=0)
        db.add(usage)

    usage.used += quantity
    db.commit()
    db.refresh(usage)
    return usage


# ----------------------------
# Usage CRUD
# ----------------------------

def get_usage(db: Session, id: UUID) -> Optional[Usage]:
    """Return a single usage row by id."""

    return get_by_id(db, Usage, id)


def get_usages(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
) -> List[Usage]:
    """Return paginated usage rows, optionally filtered by user."""

    return list_records(
        db,
        Usage,
        skip=skip,
        limit=limit,
        filters={"user_id": user_id},
    )


def create_usage(db: Session, obj_in: Any) -> Usage:
    """Create or update a usage row for a given (user_id, resource_type) pair.

    Uses SELECT FOR UPDATE so that two concurrent callers converge on a single
    row rather than both INSERTing duplicates and hitting a constraint error.
    If a row already exists the caller's ``limit_value`` (and optional ``used``)
    values are merged in.
    """

    data = _to_update_dict(obj_in)
    user_id = data.get("user_id")
    resource_type = data.get("resource_type")

    if user_id and resource_type:
        existing = (
            db.query(Usage)
            .filter(Usage.user_id == user_id, Usage.resource_type == resource_type)
            .with_for_update()  # prevent concurrent phantom inserts
            .first()
        )
        if existing is not None:
            # Merge supplied fields onto the existing row instead of inserting a duplicate
            _apply_updates(existing, data)
            db.commit()
            db.refresh(existing)
            return existing

    db_obj = Usage(**data)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_usage(db: Session, db_obj: Usage, obj_in: Any) -> Usage:
    """Update mutable fields on a usage row."""

    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_usage(db: Session, id: UUID) -> Optional[Usage]:
    """Delete a usage row by id."""

    db_obj = get_usage(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj
