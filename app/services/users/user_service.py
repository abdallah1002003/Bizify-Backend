from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models import AdminActionLog, User, UserProfile
from app.models.enums import UserRole

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
