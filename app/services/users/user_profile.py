"""
User Profile CRUD operations.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import UserProfile
from app.services.billing.billing_service import _to_update_dict, _apply_updates

logger = logging.getLogger(__name__)


def _record_admin_action(
    db: Session,
    admin_id: Optional[UUID],
    action_type: str,
    target_id: Optional[UUID],
    target_entity: str = "user_profile",
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
# UserProfile CRUD
# ----------------------------

def get_user_profile(
    db: Session,
    id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
) -> Optional[UserProfile]:
    if id is not None:
        return db.query(UserProfile).filter(UserProfile.id == id).first()
    if user_id is not None:
        return db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    return None


def get_user_profiles(db: Session, skip: int = 0, limit: int = 100) -> List[UserProfile]:
    return db.query(UserProfile).offset(skip).limit(limit).all()


def create_user_profile(db: Session, obj_in: Any) -> UserProfile:
    db_obj = UserProfile(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_user_profile(
    db: Session,
    db_obj: Optional[UserProfile] = None,
    obj_in: Any = None,
    user_id: Optional[UUID] = None,
    profile_data: Optional[Dict[str, Any]] = None,
    performer_id: Optional[UUID] = None,
) -> UserProfile:
    # Backward-compat signature support:
    # update_user_profile(db, user_id, profile_data, performer_id)
    if isinstance(db_obj, UUID):
        legacy_user_id = db_obj
        legacy_profile_data = obj_in if isinstance(obj_in, dict) else {}
        legacy_performer_id = user_id

        db_obj = get_user_profile(db, user_id=legacy_user_id)
        if db_obj is None:
            db_obj = UserProfile(user_id=legacy_user_id, bio="", preferences_json={})
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)

        _apply_updates(db_obj, legacy_profile_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        _record_admin_action(
            db,
            admin_id=legacy_performer_id,
            action_type="PROFILE_UPDATED",
            target_id=legacy_user_id,
            target_entity="user_profile",
        )
        return db_obj

    if db_obj is None:
        if user_id is None:
            raise ValueError("Either db_obj or user_id must be provided")
        db_obj = get_user_profile(db, user_id=user_id)
        if db_obj is None:
            db_obj = UserProfile(user_id=user_id, bio="", preferences_json={})
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)

    update_data = profile_data if profile_data is not None else _to_update_dict(obj_in)
    _apply_updates(db_obj, update_data)

    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)

    if performer_id is not None:
        _record_admin_action(
            db,
            admin_id=performer_id,
            action_type="PROFILE_UPDATED",
            target_id=db_obj.user_id,
            target_entity="user_profile",
        )

    return db_obj


def delete_user_profile(db: Session, id: UUID) -> Optional[UserProfile]:
    db_obj = get_user_profile(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj
