from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
import secrets
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import File, Notification, ShareLink

logger = logging.getLogger(__name__)


from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates

def _is_expired(expires_at: datetime) -> bool:
    now = _utc_now()
    if expires_at.tzinfo is None and now.tzinfo is not None:
        now = now.replace(tzinfo=None)
    return expires_at < now


# ----------------------------
# File
# ----------------------------

def get_file(db: Session, id: UUID) -> Optional[File]:
    return db.query(File).filter(File.id == id).first()


def get_files(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    owner_id: Optional[UUID] = None,
) -> List[File]:
    query = db.query(File)
    if owner_id is not None:
        query = query.filter(File.owner_id == owner_id)
    return query.offset(skip).limit(limit).all()


def create_file(db: Session, obj_in: Any) -> File:
    db_obj = File(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_file(db: Session, db_obj: File, obj_in: Any) -> File:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_file(db: Session, id: UUID) -> Optional[File]:
    db_obj = get_file(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


# ----------------------------
# ShareLink
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

    if link.expires_at is not None and _is_expired(link.expires_at):
        return None

    return link


# ----------------------------
# Notification
# ----------------------------

def get_notification(db: Session, id: UUID) -> Optional[Notification]:
    return db.query(Notification).filter(Notification.id == id).first()


def get_notifications(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
) -> List[Notification]:
    query = db.query(Notification)
    if user_id is not None:
        query = query.filter(Notification.user_id == user_id)
    return query.offset(skip).limit(limit).all()


def create_notification(db: Session, obj_in: Any) -> Notification:
    db_obj = Notification(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_notification(db: Session, db_obj: Notification, obj_in: Any) -> Notification:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_notification(db: Session, id: UUID) -> Optional[Notification]:
    db_obj = get_notification(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


# Backward compatibility aliases.
create_file_record = create_file
emit_notification = create_notification


def get_detailed_status() -> Dict[str, Any]:
    return {
        "module": "core_service",
        "status": "operational",
        "timestamp": _utc_now().isoformat(),
    }


def reset_internal_state() -> None:
    logger.info("core_service reset_internal_state called")
