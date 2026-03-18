from typing import Any, Dict

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api import dependencies as deps
from app.models.user import User
from app.schemas.settings import (
    NotificationUpdate,
    PasswordChange,
    PrivacyUpdate,
    ProfileUpdate,
    SettingsResponse,
)
from app.schemas.user_profile import UserProfileRead
from app.services.settings_service import SettingsService


router = APIRouter()


@router.get("/", response_model = SettingsResponse)
def get_my_settings(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Dict[str, Any]:
    """
    Get all current settings (profile, notifications, privacy).
    """
    user = SettingsService.get_user_settings(db, current_user)
    
    return {
        "email": user.email,
        "is_active": user.is_active,
        "last_password_change": user.last_password_change,
        "full_name": user.full_name,
        "privacy": user.privacy_settings if user.privacy_settings else None,
        "notifications": user.notification_settings if user.notification_settings else None
    }


@router.patch("/profile", response_model = UserProfileRead)
def update_my_profile(
    data: ProfileUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> UserProfileRead:
    """
    Update profile information for the authenticated user.
    """
    return SettingsService.update_profile(db, current_user, data)


@router.patch("/password")
def change_my_password(
    request: Request,
    data: PasswordChange,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Dict[str, str]:
    """
    Update password and invalidate other sessions (Global Logout).
    """
    ip = request.client.host
    return SettingsService.update_password(db, current_user, data, ip)


@router.patch("/notifications", response_model = NotificationUpdate)
def update_my_notifications(
    data: NotificationUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> NotificationUpdate:
    """
    Update notification settings for the user.
    """
    return SettingsService.update_notifications(db, current_user, data)


@router.patch("/privacy", response_model = PrivacyUpdate)
def update_my_privacy(
    data: PrivacyUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> PrivacyUpdate:
    """
    Update privacy and visibility settings for the user.
    """
    return SettingsService.update_privacy(db, current_user, data)


@router.post("/deactivate")
def deactivate_my_account(
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Dict[str, str]:
    """
    Deactivate account immediately (Soft Delete).
    """
    ip = request.client.host
    return SettingsService.deactivate_account(db, current_user, ip)


@router.delete("/")
def delete_my_account(
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Dict[str, str]:
    """
    Permanently delete/anonymize account (Hard Delete).
    """
    ip = request.client.host
    return SettingsService.delete_account(db, current_user, ip)
