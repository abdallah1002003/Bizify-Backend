"""
User CRUD operations.
"""
from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models import User, UserProfile

logger = logging.getLogger(__name__)

from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates

def _record_admin_action(
    db: Session,
    admin_id: Optional[UUID],
    action_type: str,
    target_id: Optional[UUID],
    target_entity: str = "user",
) -> None:
    from app.models import AdminActionLog
    
    if target_id is None:
        raise ValueError("target_id is required for admin log")

    log = AdminActionLog(
        admin_id=admin_id,
        action_type=action_type,
        target_entity=target_entity,
        target_id=target_id,
    )
    db.add(log)
    db.commit()


# ----------------------------
# User CRUD
# ----------------------------

def get_user(db: Session, id: UUID) -> Optional[User]:
    return db.query(User).filter(User.id == id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, obj_in: Any) -> User:
    user_data = _to_update_dict(obj_in)

    if user_data.get("password_hash"):
        user_data["password_hash"] = get_password_hash(user_data["password_hash"])

    db_obj = User(**user_data)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)

    # Ensure profile exists for new users.
    if not db.query(UserProfile).filter(UserProfile.user_id == db_obj.id).first():
        profile = UserProfile(user_id=db_obj.id, bio="", preferences_json={})
        db.add(profile)
        db.commit()

    _record_admin_action(
        db,
        admin_id=db_obj.id,
        action_type="USER_CREATED",
        target_id=db_obj.id,
        target_entity="user",
    )
    return db_obj


def update_user(db: Session, db_obj: User, obj_in: Any) -> User:
    update_data = _to_update_dict(obj_in)

    if update_data.get("password_hash"):
        update_data["password_hash"] = get_password_hash(update_data["password_hash"])

    _apply_updates(db_obj, update_data)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_user(db: Session, id: UUID) -> Optional[User]:
    db_obj = get_user(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


def mask_user_data(user: User) -> Dict[str, Any]:
    masked = "***"
    email = user.email or ""
    if "@" in email:
        username, domain = email.split("@", 1)
        username = (username[:2] + masked) if username else masked
        email = f"{username}@{domain}"
    return {
        "id": user.id,
        "name": user.name,
        "email": email,
        "role": user.role,
        "is_active": user.is_active,
    }
