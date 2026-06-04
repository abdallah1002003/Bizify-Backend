from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.privacy_setting import ProfileVisibility


class PasswordChange(BaseModel):
    """
    Pydantic model for a password change request.
    """

    current_password: str
    new_password: str = Field(..., min_length = 8)
    confirm_password: str


class ProfileUpdate(BaseModel):
    """
    Pydantic model for updating a user profile.
    """

    full_name: Optional[str] = None
    bio: Optional[str] = None
    interests: Optional[list[str]] = None


class PrivacyUpdate(BaseModel):
    """
    Pydantic model for updating privacy preferences.
    """

    visibility: Optional[ProfileVisibility] = None
    show_contact_info: Optional[bool] = None

    model_config = ConfigDict(from_attributes = True)


class NotificationUpdate(BaseModel):
    """
    Pydantic model for updating notification preferences.
    """

    is_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None

    model_config = ConfigDict(from_attributes = True)


class LanguageUpdate(BaseModel):
    """
    Pydantic model for updating the user's preferred language.
    """

    preferred_language: str = Field(..., pattern="^(en|ar)$")


class SettingsResponse(BaseModel):
    """
    Pydantic model for reading the full user settings.
    """

    email: str
    is_active: bool
    last_password_change: Optional[datetime]
    full_name: Optional[str]
    preferred_language: str = "en"
    privacy: Optional[PrivacyUpdate]
    notifications: Optional[NotificationUpdate]

    model_config = ConfigDict(from_attributes = True)
