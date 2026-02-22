"""
Share Link CRUD operations and validation.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
import secrets
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import ShareLink

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
# ShareLink CRUD
# ----------------------------

def get_share_link(db: Session, id: UUID) -> Optional[ShareLink]:
    return db.query(ShareLink).filter(ShareLink.id == id).first()


def get_share_links(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    created_by: Optional[UUID] = None,
) -> List[ShareLink]:
    query = db.query(ShareLink)
    if created_by is not None:
        query = query.filter(ShareLink.created_by == created_by)
    return query.offset(skip).limit(limit).all()


def create_share_link(
    db: Session,
    obj_in: Any = None,
    business_id: Optional[UUID] = None,
    idea_id: Optional[UUID] = None,
    creator_id: Optional[UUID] = None,
    expires_in_days: int = 7,
) -> ShareLink:
    if obj_in is not None:
        data = _to_update_dict(obj_in)
    else:
        data = {
            "business_id": business_id,
            "idea_id": idea_id,
            "created_by": creator_id,
            "token": secrets.token_urlsafe(32),
            "is_public": False,
            "expires_at": _utc_now() + timedelta(days=expires_in_days),
        }

    if not data.get("token"):
        data["token"] = secrets.token_urlsafe(32)

    db_obj = ShareLink(**data)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_share_link(db: Session, db_obj: ShareLink, obj_in: Any) -> ShareLink:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_share_link(db: Session, id: UUID) -> Optional[ShareLink]:
    db_obj = get_share_link(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


def validate_share_link(db: Session, token: str) -> Optional[ShareLink]:
    link = db.query(ShareLink).filter(ShareLink.token == token).first()
    if link is None:
        return None

    if link.expires_at is not None and link.expires_at < _utc_now():
        return None

    return link
