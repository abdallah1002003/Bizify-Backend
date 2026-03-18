from datetime import datetime
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.audit_log import AuditLog
from app.models.notification_setting import NotificationSetting
from app.models.privacy_setting import PrivacySetting
from app.models.user import User
from app.models.user_profile import UserProfile
from app.schemas.settings import NotificationUpdate, PasswordChange, ProfileUpdate, PrivacyUpdate


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
        if not user.privacy_settings:
            privacy = PrivacySetting(user_id = user.id)
            db.add(privacy)
            db.commit()
            db.refresh(user)

        return user

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

        log = AuditLog(user_id = user.id, action = "PASSWORD_CHANGE", ip_address = ip)
        db.add(log)
        db.commit()

        return {"message": "Password updated successfully. All other sessions revoked."}

    @staticmethod
    def deactivate_account(db: Session, user: User, ip: Optional[str] = None) -> dict:
        """
        Deactivates the user account and logs the action for audit purposes.
        """
        user.is_active = False

        log = AuditLog(user_id = user.id, action = "ACCOUNT_DEACTIVATION", ip_address = ip)
        db.add(log)
        db.commit()

        return {"message": "Account deactivated and session terminated."}

    @staticmethod
    def update_profile(db: Session, user: User, data: ProfileUpdate) -> UserProfile:
        """
        Updates the basic profile fields for a user (name, bio, interests).
        """
        # Full name is on the User model
        if data.full_name is not None:
            user.full_name = data.full_name

        if not user.profile:
            user.profile = UserProfile(user_id = user.id)
            db.add(user.profile)

        if data.bio is not None:
            user.profile.bio = data.bio

        # Interests are stored as interests_json on UserProfile
        if data.interests is not None:
            user.profile.interests_json = data.interests

        db.commit()
        db.refresh(user.profile)

        return user.profile

    @staticmethod
    def update_privacy(db: Session, user: User, data: PrivacyUpdate) -> PrivacySetting:
        """
        Updates the user's privacy visibility and contact info settings.
        """
        if not user.privacy_settings:
            privacy = PrivacySetting(user_id = user.id)
            db.add(privacy)
        else:
            privacy = user.privacy_settings

        if data.visibility is not None:
            privacy.visibility = data.visibility

        if data.show_contact_info is not None:
            privacy.show_contact_info = data.show_contact_info

        db.commit()
        db.refresh(privacy)

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
        if not user.notification_settings:
            settings = NotificationSetting(user_id = user.id)
            db.add(settings)
        else:
            settings = user.notification_settings

        if data.is_enabled is not None:
            settings.is_enabled = data.is_enabled

        if data.email_enabled is not None:
            settings.email_enabled = data.email_enabled

        if data.push_enabled is not None:
            settings.push_enabled = data.push_enabled

        db.commit()
        db.refresh(settings)

        return settings

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

        log = AuditLog(user_id = user.id, action = "ACCOUNT_DELETION", ip_address = ip)
        db.add(log)
        db.commit()

        return {"message": "Account data anonymized and permanently disabled."}
