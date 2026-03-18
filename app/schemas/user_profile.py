import uuid
from datetime import datetime
from typing import Any, Optional, List, Dict

from pydantic import BaseModel, ConfigDict, field_validator


class UserProfileBase(BaseModel):
    """
    Base Pydantic model for User Profile data.
    """

    bio: Optional[str] = None
    skills_json: Optional[Any] = None
    interests_json: Optional[Any] = None
    preferences_json: Optional[Any] = None
    risk_profile_json: Optional[Any] = None
    onboarding_completed: Optional[bool] = False


class UserProfileCreate(UserProfileBase):
    """
    Pydantic model for creating a User Profile.
    """

    user_id: uuid.UUID


class UserProfileUpdate(UserProfileBase):
    """
    Pydantic model for updating a User Profile.
    """

    bio: Optional[str] = None
    skills_json: Optional[List[Dict[str, Any]]] = None
    interests_json: Optional[List[str]] = None
    preferences_json: Optional[Dict[str, Any]] = None

    @field_validator("skills_json")
    @classmethod
    def validate_skills(cls, v: Optional[List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
        """
        Validates that each skill has a name and a rating between 1 and 5.
        """
        if v is None:
            return v
            
        for skill in v:
            if "name" not in skill or "rating" not in skill:
                raise ValueError("Each skill must have a 'name' and a 'rating'")
                
            if not (1 <= skill["rating"] <= 5):
                raise ValueError(f"Rating for skill '{skill['name']}' must be between 1 and 5")
                
        return v


class UserProfileRead(UserProfileBase):
    """
    Pydantic model for reading User Profile data.
    """

    id: uuid.UUID
    user_id: uuid.UUID
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes = True)
