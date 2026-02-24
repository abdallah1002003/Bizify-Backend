from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, Any, Dict
from uuid import UUID

class UserProfileBase(BaseModel):
    user_id: UUID
    bio: str
    skills_json: Optional[dict] = None
    interests_json: Optional[dict] = None
    preferences_json: Optional[dict] = None
    risk_profile_json: Optional[dict] = None
    onboarding_completed: Optional[bool] = None
    
    @field_validator('skills_json', 'interests_json', 'preferences_json', 'risk_profile_json', mode='before')
    @classmethod
    def validate_json_fields(cls, v):
        """Validate JSON fields at input time."""
        if v is None:
            return {}
        if not isinstance(v, dict):
            raise ValueError(f"JSON field must be a dictionary, got {type(v).__name__}")
        # Ensure all values are JSON-serializable
        try:
            import json
            json.dumps(v)
        except (TypeError, ValueError) as e:
            raise ValueError(f"JSON field contains non-serializable values: {e}")
        return v

class UserProfileCreate(BaseModel):
    user_id: UUID
    bio: str
    skills_json: Optional[dict] = None
    interests_json: Optional[dict] = None
    preferences_json: Optional[dict] = None
    risk_profile_json: Optional[dict] = None
    onboarding_completed: Optional[bool] = None
    
    @field_validator('skills_json', 'interests_json', 'preferences_json', 'risk_profile_json', mode='before')
    @classmethod
    def validate_json_fields(cls, v):
        """Validate JSON fields at input time."""
        if v is None:
            return {}
        if not isinstance(v, dict):
            raise ValueError(f"JSON field must be a dictionary, got {type(v).__name__}")
        try:
            import json
            json.dumps(v)
        except (TypeError, ValueError) as e:
            raise ValueError(f"JSON field contains non-serializable values: {e}")
        return v

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
    
    @field_validator('skills_json', 'interests_json', 'preferences_json', 'risk_profile_json', mode='before')
    @classmethod
    def validate_json_fields(cls, v):
        """Validate JSON fields at input time."""
        if v is None:
            return None
        if not isinstance(v, dict):
            raise ValueError(f"JSON field must be a dictionary, got {type(v).__name__}")
        try:
            import json
            json.dumps(v)
        except (TypeError, ValueError) as e:
            raise ValueError(f"JSON field contains non-serializable values: {e}")
        return v

class UserProfileResponse(UserProfileBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
