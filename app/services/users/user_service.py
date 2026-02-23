from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models import AdminActionLog, User, UserProfile
from app.models.enums import UserRole
from app.services.billing.billing_service import _utc_now, _to_update_dict, _apply_updates

logger = logging.getLogger(__name__)


def _record_admin_action(
    db: Session,
    admin_id: Optional[UUID],
    action_type: str,
    target_id: Optional[UUID],
    target_entity: str = "user",
    auto_commit: bool = True
) -> AdminActionLog:
    if target_id is None:
        raise ValueError("target_id is required for admin log")

    log = AdminActionLog(
        admin_id=admin_id,
        action_type=action_type,
        target_entity=target_entity,
        target_id=target_id,
    )
    db.add(log)
    if auto_commit:
        db.commit()
        db.refresh(log)
    else:
        db.flush()
    return log


# ----------------------------
# User CRUD
# ----------------------------

def get_user(db: Session, id: UUID) -> Optional[User]:
    return db.query(User).filter(User.id == id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, obj_in: Union[Dict[str, Any], Any]) -> User:
    try:
        user_data = _to_update_dict(obj_in)

        if "password" in user_data:
            user_data["password_hash"] = get_password_hash(user_data.pop("password"))
        elif "password_hash" in user_data:
            user_data["password_hash"] = get_password_hash(user_data["password_hash"])

        user_data.setdefault("role", UserRole.ENTREPRENEUR)

        db_obj = User(**user_data)
        db.add(db_obj)
        db.flush()

        # Ensure profile exists for new users.
        if not db.query(UserProfile).filter(UserProfile.user_id == db_obj.id).first():
            profile = UserProfile(user_id=db_obj.id, bio="", preferences_json={})
            db.add(profile)

        _record_admin_action(
            db,
            admin_id=db_obj.id,
            action_type="USER_CREATED",
            target_id=db_obj.id,
            target_entity="user",
            auto_commit=False,
        )
        db.commit()
        db.refresh(db_obj)
        logger.info(f"Successfully created user: {db_obj.email} (ID: {db_obj.id})")
        return db_obj
    except Exception as e:
        db.rollback()
        logger.error(f"Transaction failed during create_user: {e}")
        raise


def update_user(db: Session, db_obj: User, obj_in: Any) -> User:
    update_data = _to_update_dict(obj_in)

    if "password" in update_data:
        update_data["password_hash"] = get_password_hash(update_data.pop("password"))
    elif "password_hash" in update_data:
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
    db_obj: UserProfile,
    obj_in: Any,
    performer_id: Optional[UUID] = None,
) -> UserProfile:
    """Update a user profile explicitly by passing the UserProfile db object."""
    update_data = _to_update_dict(obj_in)
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


def update_user_profile_by_user_id(
    db: Session,
    user_id: UUID,
    profile_data: Dict[str, Any],
    performer_id: Optional[UUID] = None,
) -> UserProfile:
    """Update a user profile by resolving the user_id first."""
    db_obj = get_user_profile(db, user_id=user_id)
    if db_obj is None:
        db_obj = UserProfile(user_id=user_id, bio="", preferences_json={})
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

    _apply_updates(db_obj, profile_data)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)

    _record_admin_action(
        db,
        admin_id=performer_id,
        action_type="PROFILE_UPDATED",
        target_id=user_id,
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


# ----------------------------
# AdminActionLog CRUD
# ----------------------------

def get_admin_action_log(db: Session, id: UUID) -> Optional[AdminActionLog]:
    return db.query(AdminActionLog).filter(AdminActionLog.id == id).first()


def get_admin_action_logs(db: Session, skip: int = 0, limit: int = 100) -> List[AdminActionLog]:
    return (
        db.query(AdminActionLog)
        .order_by(AdminActionLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_admin_action_log(db: Session, obj_in: Any) -> AdminActionLog:
    data = _to_update_dict(obj_in)
    db_obj = AdminActionLog(**data)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_admin_action_log(db: Session, db_obj: AdminActionLog, obj_in: Any) -> AdminActionLog:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_admin_action_log(db: Session, id: UUID) -> Optional[AdminActionLog]:
    db_obj = get_admin_action_log(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


# Backward-compatible alias used by older code.
def get_admin_logs(db: Session, skip: int = 0, limit: int = 100) -> List[AdminActionLog]:
    return get_admin_action_logs(db, skip=skip, limit=limit)


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


def get_detailed_status() -> Dict[str, Any]:
    return {
        "module": "user_service",
        "status": "operational",
        "timestamp": _utc_now().isoformat(),
    }


def reset_internal_state() -> None:
    logger.info("user_service reset_internal_state called")
