from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.notification_setting import NotificationSetting
from app.models.privacy_setting import PrivacySetting
from app.models.user import User
from app.models.user_profile import UserProfile
from app.schemas.settings import NotificationUpdate, PasswordChange, ProfileUpdate, PrivacyUpdate
from app.repositories.privacy_repo import privacy_repo
from app.repositories.admin_repo import audit_repo
from app.repositories.user_repo import user_repo
from app.repositories.notification_repo import notification_repo
from app.repositories.profile_repo import profile_repo


class SettingsService:
    """
    Service class for managing user account settings.
    Handles password changes, profile updates, privacy, notifications, and account lifecycle.
    """

    @staticmethod
    def get_user_settings(db: Session, user: User) -> User:
        """
        Retrieves user settings, creating a default privacy record if one does not exist.
        """
        privacy_repo.get_or_create(db, user.id)
        return user_repo.get(db, user.id) or user

    @staticmethod
    def update_password(
        db: Session,
        user: User,
        data: PasswordChange,
        ip: Optional[str] = None
    ) -> dict:
        """
        Updates user password after verifying the current one and logging the action.
        """
        if data.new_password != data.confirm_password:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = "Passwords do not match"
            )

        if not verify_password(data.current_password, user.password_hash):
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = "Incorrect current password"
            )

        user.password_hash = get_password_hash(data.new_password)
        user.last_password_change = datetime.utcnow()
        user_repo.save(db, db_obj=user)

        audit_repo.log_action(db, user.id, "PASSWORD_CHANGE", ip)

        return {"message": "Password updated successfully. All other sessions revoked."}

    @staticmethod
    def deactivate_account(db: Session, user: User, ip: Optional[str] = None) -> dict:
        """
        Deactivates the user account and logs the action for audit purposes.
        """
        user.is_active = False
        user_repo.save(db, db_obj=user)

        audit_repo.log_action(db, user.id, "ACCOUNT_DEACTIVATION", ip)

        return {"message": "Account deactivated and session terminated."}

    @staticmethod
    def update_profile(db: Session, user: User, data: ProfileUpdate) -> UserProfile:
        """
        Updates the basic profile fields for a user (name, bio, interests).
        """
        user_changed = False
        if data.full_name is not None and data.full_name != user.full_name:
            user.full_name = data.full_name
            user_changed = True

        profile = profile_repo.get_or_create(db, user.id)
        
        update_data = {}
        if data.bio is not None:
            update_data["bio"] = data.bio

        if data.interests is not None:
            update_data["interests_json"] = data.interests

        if not user_changed and not update_data:
            return profile

        if user_changed:
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
        """
        Updates the user's privacy visibility and contact info settings.
        """
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
        data: NotificationUpdate
    ) -> NotificationSetting:
        """
        Updates the user's notification channel preferences.
        """
        update_data = {}
        if data.is_enabled is not None:
            update_data["is_enabled"] = data.is_enabled

        if data.email_enabled is not None:
            update_data["email_enabled"] = data.email_enabled

        if data.push_enabled is not None:
            update_data["push_enabled"] = data.push_enabled

        return notification_repo.update_settings(db, user.id, update_data)

    @staticmethod
    def delete_account(db: Session, user: User, ip: Optional[str] = None) -> dict:
        """
        Permanently anonymizes user data to comply with data erasure requirements.
        """
        user.email = f"deleted_{user.id}@anonymous.com"
        user.password_hash = "DELETED"
        user.is_active = False

        if user.profile:
            user.profile.full_name = "Anonymous User"
            user.profile.bio = None

        user_repo.save(db, db_obj=user)
        
        audit_repo.log_action(db, user.id, "ACCOUNT_DELETION", ip)

        return {"message": "Account data anonymized and permanently disabled."}
