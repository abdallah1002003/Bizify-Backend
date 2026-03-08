from app.models.enums import ApprovalStatus, PartnerType
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
# ruff: noqa: B904
from typing import Optional, Any, Dict
from uuid import UUID

class PartnerProfileBase(BaseModel):
    user_id: UUID
    partner_type: PartnerType
    company_name: Optional[str] = None
    description: Optional[str] = None
    services_json: Optional[dict] = None
    experience_json: Optional[dict] = None
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    approved_by: Optional[UUID] = None

class PartnerProfileCreate(BaseModel):
    user_id: UUID
    partner_type: PartnerType
    company_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    services_json: Optional[dict] = None
    experience_json: Optional[dict] = None
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    approved_by: Optional[UUID] = None
    
    @field_validator('services_json', 'experience_json', mode='before')
    @classmethod
    def validate_json_fields(cls, v: Any) -> Dict[str, Any]:
        """Validate JSON fields at input time."""
        if v is None:
            return {}
        if not isinstance(v, dict):
            raise ValueError(f"JSON field must be a dictionary, got {type(v).__name__}")
        try:
            import json
            json.dumps(v)
        except (TypeError, ValueError) as e:
            raise ValueError(f"JSON field contains non-serializable values: {e}") from e
        return v

class PartnerProfileUpdate(BaseModel):
    user_id: Optional[UUID] = None
    partner_type: Optional[PartnerType] = None
    company_name: Optional[str] = None
    description: Optional[str] = None
    services_json: Optional[dict] = None
    experience_json: Optional[dict] = None
    approval_status: Optional[ApprovalStatus] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    @field_validator('services_json', 'experience_json', mode='before')
    @classmethod
    def validate_json_fields(cls, v: Any) -> Optional[Dict[str, Any]]:
        """Validate JSON fields at input time."""
        if v is None:
            return None
        if not isinstance(v, dict):
            raise ValueError(f"JSON field must be a dictionary, got {type(v).__name__}")
        try:
            import json
            json.dumps(v)
        except (TypeError, ValueError) as e:
            raise ValueError(f"JSON field contains non-serializable values: {e}") from e
        return v

class PartnerProfileResponse(PartnerProfileBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
