from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, Any

class UserProfileBase(BaseModel):
    bio: Optional[str] = None
    skills_json: Optional[Any] = None
    interests_json: Optional[Any] = None
    preferences_json: Optional[Any] = None
    risk_profile_json: Optional[Any] = None
    onboarding_completed: Optional[bool] = False

class UserProfileCreate(UserProfileBase):
    user_id: UUID

class UserProfileUpdate(UserProfileBase):
    pass

class UserProfileRead(UserProfileBase):
    id: UUID
    user_id: UUID
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
