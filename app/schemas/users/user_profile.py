from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID

class UserProfileBase(BaseModel):
    user_id: UUID
    bio: str
    skills_json: Optional[dict] = None
    interests_json: Optional[dict] = None
    preferences_json: Optional[dict] = None
    risk_profile_json: Optional[dict] = None
    onboarding_completed: Optional[bool] = None

class UserProfileCreate(BaseModel):
    user_id: UUID
    bio: str
    skills_json: Optional[dict] = None
    interests_json: Optional[dict] = None
    preferences_json: Optional[dict] = None
    risk_profile_json: Optional[dict] = None
    onboarding_completed: Optional[bool] = None

class UserProfileUpdate(BaseModel):
    user_id: Optional[UUID] = None
    bio: Optional[str] = None
    skills_json: Optional[dict] = None
    interests_json: Optional[dict] = None
    preferences_json: Optional[dict] = None
    risk_profile_json: Optional[dict] = None
    onboarding_completed: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class UserProfileResponse(UserProfileBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
