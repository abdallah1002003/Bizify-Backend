from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, Any
from app.models.partner_profile import PartnerType, ApprovalStatus

class PartnerProfileBase(BaseModel):
    partner_type: PartnerType
    company_name: Optional[str] = None
    description: Optional[str] = None
    services_json: Optional[Any] = None
    experience_json: Optional[Any] = None

class PartnerProfileCreate(PartnerProfileBase):
    user_id: UUID

class PartnerProfileUpdate(BaseModel):
    partner_type: Optional[PartnerType] = None
    company_name: Optional[str] = None
    description: Optional[str] = None
    services_json: Optional[Any] = None
    experience_json: Optional[Any] = None
    approval_status: Optional[ApprovalStatus] = None

class PartnerProfileRead(PartnerProfileBase):
    id: UUID
    user_id: UUID
    approval_status: ApprovalStatus
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
