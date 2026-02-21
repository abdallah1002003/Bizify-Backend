from app.models.enums import ApprovalStatus, PartnerType
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
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

class PartnerProfileResponse(PartnerProfileBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
