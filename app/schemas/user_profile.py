import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.user_profile import GuideStatus


class UserProfileBase(BaseModel):
    """Shared fields for user profile payloads."""

    bio: Optional[str] = None
    onboarding_completed: Optional[bool] = False


class UserProfileCreate(UserProfileBase):
    """Create payload including owner."""

    user_id: uuid.UUID
    skills_json: Optional[Any] = None
    questionnaire_json: Optional[Any] = None


class UserProfileUpdate(UserProfileBase):
    """Partial update for PATCH/POST profile endpoints."""

    bio: Optional[str] = None
    skills_json: Optional[List[Dict[str, Any]]] = None
    questionnaire_json: Optional[Dict[str, Any]] = None

    @field_validator("skills_json")
    @classmethod
    def validate_skills(
        cls, v: Optional[List[Dict[str, Any]]]
    ) -> Optional[List[Dict[str, Any]]]:
        if v is None:
            return v
        for skill in v:
            if "name" not in skill or "rating" not in skill:
                raise ValueError("Each skill must have a 'name' and a 'rating'")
            if not (1 <= skill["rating"] <= 5):
                raise ValueError(
                    f"Rating for skill '{skill['name']}' must be between 1 and 5"
                )
        return v


class UserProfileRead(UserProfileBase):
    """API read model aligned with `user_profiles` columns."""

    id: uuid.UUID
    user_id: uuid.UUID
    guide_status: GuideStatus
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
