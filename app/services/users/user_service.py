# ruff: noqa: E402
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union, cast
from uuid import UUID

from sqlalchemy.orm import Session, joinedload
from fastapi import Depends

from app.db.database import get_db

from app.core.security import get_password_hash
from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates
from app.models import AdminActionLog, User, UserProfile
from app.models.enums import UserRole
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class UserService(BaseService):
    """Service for managing user accounts, profiles, and admin logs."""

    def _record_admin_action(
        self,
        admin_id: Optional[UUID],
        action_type: str,
        target_id: Optional[UUID],
        target_entity: str = "user",
        auto_commit: bool = True
    ) -> AdminActionLog:
        """Records an administrative action in the audit log."""
        if target_id is None:
            raise ValueError("target_id is required for admin log")

        log = AdminActionLog(
            admin_id=admin_id,
            action_type=action_type,
            target_entity=target_entity,
            target_id=target_id,
        )
        self.db.add(log)
        if auto_commit:
            self.db.commit()
            self.db.refresh(log)
        else:
            self.db.flush()
        return log

    # ----------------------------
    # User CRUD
    # ----------------------------

    def get_user(self, id: UUID) -> Optional[User]:
        """Retrieves a user by their unique UUID."""
        return self.db.query(User).options(joinedload(User.profile)).filter(User.id == id).first()  # type: ignore[no-any-return]

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Retrieves a user by their registered email address."""
        return self.db.query(User).options(joinedload(User.profile)).filter(User.email == email).first()  # type: ignore[no-any-return]

    def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Retrieves a list of users with pagination."""
        return self.db.query(User).options(joinedload(User.profile)).offset(skip).limit(limit).all()  # type: ignore[no-any-return]

    def create_user(self, obj_in: Union[Dict[str, Any], Any]) -> User:
        """Creates a new user and an associated empty profile."""
        try:
            user_data = _to_update_dict(obj_in)

            if "password" in user_data:
                user_data["password_hash"] = get_password_hash(user_data.pop("password"))
            elif "password_hash" in user_data:
                user_data["password_hash"] = get_password_hash(user_data["password_hash"])

            user_data.setdefault("role", UserRole.ENTREPRENEUR)

            db_obj = User(**user_data)
            self.db.add(db_obj)
            self.db.flush()

            # Ensure profile exists for new users.
            if not self.db.query(UserProfile).filter(UserProfile.user_id == db_obj.id).first():
                profile = UserProfile(user_id=db_obj.id, bio="", preferences_json={})
                self.db.add(profile)

            self._record_admin_action(
                admin_id=cast(UUID, db_obj.id),
                action_type="USER_CREATED",
                target_id=cast(UUID, db_obj.id),
                target_entity="user",
                auto_commit=False,
            )
            self.db.commit()
            self.db.refresh(db_obj)
            logger.info(f"Successfully created user: {db_obj.email} (ID: {db_obj.id})")
            return db_obj
        except Exception as e:
            self.db.rollback()
            logger.error(f"Transaction failed during create_user: {e}")
            raise

    def update_user(self, db_obj: User, obj_in: Any) -> User:
        """Updates an existing user's information."""
        update_data = _to_update_dict(obj_in)

        if "password" in update_data:
            update_data["password_hash"] = get_password_hash(update_data.pop("password"))
        elif "password_hash" in update_data:
            update_data["password_hash"] = get_password_hash(update_data["password_hash"])

        _apply_updates(db_obj, update_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete_user(self, id: UUID) -> Optional[User]:
        """Deletes a user and records the administrative action."""
        db_obj = self.get_user(id=id)
        if not db_obj:
            return None

        self._record_admin_action(admin_id=None, action_type="USER_DELETED", target_id=id, auto_commit=False)
        self.db.delete(db_obj)
        self.db.commit()
        return db_obj

    # ----------------------------
    # UserProfile CRUD
    # ----------------------------

    def get_user_profile(
        self,
        id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
    ) -> Optional[UserProfile]:
        """Retrieves a user profile by profile ID or user ID."""
        if id is not None:
            return self.db.query(UserProfile).filter(UserProfile.id == id).first()  # type: ignore[no-any-return]
        if user_id is not None:
            return self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()  # type: ignore[no-any-return]
        return None

    def get_user_profiles(self, skip: int = 0, limit: int = 100) -> List[UserProfile]:
        """Retrieves multiple user profiles with pagination."""
        return self.db.query(UserProfile).offset(skip).limit(limit).all()  # type: ignore[no-any-return]

    def create_user_profile(self, obj_in: Any) -> UserProfile:
        """Creates a new user profile manually."""
        db_obj = UserProfile(**_to_update_dict(obj_in))
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update_user_profile(
        self,
        db_obj: UserProfile,
        obj_in: Any,
        performer_id: Optional[UUID] = None,
    ) -> UserProfile:
        """Updates an existing user profile record."""
        update_data = _to_update_dict(obj_in)
        _apply_updates(db_obj, update_data)

        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)

        if performer_id is not None:
            self._record_admin_action(
                admin_id=performer_id,
                action_type="PROFILE_UPDATED",
                target_id=cast(UUID, db_obj.user_id),
                target_entity="user_profile",
            )

        return db_obj

    def update_user_profile_by_user_id(
        self,
        user_id: UUID,
        profile_data: Dict[str, Any],
        performer_id: Optional[UUID] = None,
    ) -> UserProfile:
        """Updates a user profile by resolving it via user_id."""
        db_obj = self.get_user_profile(user_id=user_id)
        if db_obj is None:
            db_obj = UserProfile(user_id=user_id, bio="", preferences_json={})
            self.db.add(db_obj)
            self.db.commit()
            self.db.refresh(db_obj)

        _apply_updates(db_obj, profile_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)

        self._record_admin_action(
            admin_id=performer_id,
            action_type="PROFILE_UPDATED",
            target_id=cast(UUID, user_id),
            target_entity="user_profile",
        )
        return db_obj

    def delete_user_profile(self, id: UUID) -> Optional[UserProfile]:
        """Deletes a user profile record."""
        db_obj = self.get_user_profile(id=id)
        if not db_obj:
            return None

        self.db.delete(db_obj)
        self.db.commit()
        return db_obj

    # ----------------------------
    # AdminActionLog CRUD
    # ----------------------------

    def get_admin_action_log(self, id: UUID) -> Optional[AdminActionLog]:
        """Retrieves a specific admin action log entry."""
        return self.db.query(AdminActionLog).filter(AdminActionLog.id == id).first()  # type: ignore[no-any-return]

    def get_admin_action_logs(self, skip: int = 0, limit: int = 100) -> List[AdminActionLog]:
        """Retrieves admin action logs with pagination, newest first."""
        return (  # type: ignore[no-any-return]
            self.db.query(AdminActionLog)
            .order_by(AdminActionLog.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_admin_action_log(self, obj_in: Any) -> AdminActionLog:
        """Creates a new admin action log entry."""
        data = _to_update_dict(obj_in)
        db_obj = AdminActionLog(**data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update_admin_action_log(self, db_obj: AdminActionLog, obj_in: Any) -> AdminActionLog:
        """Updates an existing admin action log entry."""
        _apply_updates(db_obj, _to_update_dict(obj_in))
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete_admin_action_log(self, id: UUID) -> Optional[AdminActionLog]:
        """Deletes an admin action log entry."""
        db_obj = self.get_admin_action_log(id=id)
        if not db_obj:
            return None

        self.db.delete(db_obj)
        self.db.commit()
        return db_obj


# ----------------------------
# Legacy/Utility functions (maintained for backward compatibility if needed)
# ----------------------------

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Dependency provider for UserService."""
    return UserService(db)

# Legacy aliases - eventually migrate away from these
def get_user(db: Session, id: UUID) -> Optional[User]:
    return UserService(db).get_user(id)

def create_user(db: Session, obj_in: Any) -> User:
    return UserService(db).create_user(obj_in)

def update_user(db: Session, db_obj: User, obj_in: Any) -> User:
    return UserService(db).update_user(db_obj, obj_in)

def get_detailed_status() -> Dict[str, Any]:
    return {
        "module": "user_service",
        "status": "operational",
        "timestamp": _utc_now().isoformat(),
    }
