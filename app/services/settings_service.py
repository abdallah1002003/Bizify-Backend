from datetime import datetime
from typing import Dict, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.notification_setting import NotificationSetting
from app.models.privacy_setting import PrivacySetting
from app.models.user import User
from app.models.user_profile import UserProfile
from app.repositories.admin_repo import audit_repo
from app.repositories.notification_repo import notification_repo
from app.repositories.privacy_repo import privacy_repo
from app.repositories.profile_repo import profile_repo
from app.repositories.user_repo import user_repo
from app.schemas.settings import NotificationUpdate, PasswordChange, PrivacyUpdate, ProfileUpdate


class SettingsService:
    """User account settings and lifecycle workflows."""

    @staticmethod
    def get_user_settings(db: Session, user: User) -> User:
        """Fetch user settings, creating privacy defaults when missing."""
        privacy_repo.get_or_create(db, user.id)
        return user_repo.get(db, user.id) or user

    @staticmethod
    def update_password(
        db: Session,
        user: User,
        data: PasswordChange,
        ip: Optional[str] = None,
    ) -> Dict[str, str]:
        """Update the user's password after validating the current one."""
        if data.new_password != data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match",
            )

        if not verify_password(data.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password",
            )

        user.password_hash = get_password_hash(data.new_password)
        user.last_password_change = datetime.utcnow()
        user_repo.save(db, db_obj=user, commit=False, refresh=False)
        audit_repo.log_action(
            db,
            user.id,
            "PASSWORD_CHANGE",
            ip,
            commit=False,
        )
        db.commit()
        db.refresh(user)

        return {"message": "Password updated successfully. All other sessions revoked."}

    @staticmethod
    def deactivate_account(
        db: Session,
        user: User,
        ip: Optional[str] = None,
    ) -> Dict[str, str]:
        """Deactivate the user's account and record the action."""
        user.is_active = False
        user_repo.save(db, db_obj=user, commit=False, refresh=False)
        audit_repo.log_action(
            db,
            user.id,
            "ACCOUNT_DEACTIVATION",
            ip,
            commit=False,
        )
        db.commit()
        db.refresh(user)

        return {"message": "Account deactivated and session terminated."}

    @staticmethod
    def update_profile(db: Session, user: User, data: ProfileUpdate) -> UserProfile:
        """Update the user's public profile and basic account name."""
        has_user_changes = False
        if data.full_name is not None and data.full_name != user.full_name:
            user.full_name = data.full_name
            has_user_changes = True

        profile = profile_repo.get_or_create(db, user.id)
        update_data = {}
        if data.bio is not None:
            update_data["bio"] = data.bio

        if data.interests is not None:
            update_data["interests_json"] = data.interests

        if not has_user_changes and not update_data:
            return profile

        if has_user_changes:
            user_repo.save(db, db_obj=user, commit=False, refresh=False)

        if update_data:
            profile = profile_repo.update(
                db,
                db_obj=profile,
                obj_in=update_data,
                commit=False,
                refresh=False,
            )

        db.commit()
        db.refresh(user)
        db.refresh(profile)
        return profile

    @staticmethod
    def update_privacy(db: Session, user: User, data: PrivacyUpdate) -> PrivacySetting:
        """Update privacy preferences for a user."""
        privacy = privacy_repo.get_or_create(db, user.id)
        update_data = {}
        if data.visibility is not None:
            update_data["visibility"] = data.visibility

        if data.show_contact_info is not None:
            update_data["show_contact_info"] = data.show_contact_info

        if update_data:
            privacy = privacy_repo.update(db, db_obj=privacy, obj_in=update_data)

        return privacy

    @staticmethod
    def update_notifications(
        db: Session,
        user: User,
        data: NotificationUpdate,
    ) -> NotificationSetting:
        """Update notification delivery preferences."""
        update_data = {}
        if data.is_enabled is not None:
            update_data["is_enabled"] = data.is_enabled

        if data.email_enabled is not None:
            update_data["email_enabled"] = data.email_enabled

        if data.push_enabled is not None:
            update_data["push_enabled"] = data.push_enabled

        return notification_repo.update_settings(db, user.id, update_data)

    @staticmethod
    def delete_account(
        db: Session,
        user: User,
        ip: Optional[str] = None,
    ) -> Dict[str, str]:
        """Anonymize a user account and disable access permanently."""
        user.email = f"deleted_{user.id}@anonymous.com"
        user.full_name = "Anonymous User"
        user.password_hash = "DELETED"
        user.is_active = False

        if user.profile:
            user.profile.bio = None

        user_repo.save(db, db_obj=user, commit=False, refresh=False)
        audit_repo.log_action(
            db,
            user.id,
            "ACCOUNT_DELETION",
            ip,
            commit=False,
        )
        db.commit()
        db.refresh(user)

        return {"message": "Account data anonymized and permanently disabled."}
