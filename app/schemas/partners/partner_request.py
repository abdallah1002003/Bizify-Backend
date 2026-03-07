from app.models.enums import RequestStatus
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID

class PartnerRequestBase(BaseModel):
    business_id: UUID
    partner_id: UUID
    requested_by: Optional[UUID] = None
    status: RequestStatus = RequestStatus.PENDING

class PartnerRequestCreate(BaseModel):
    business_id: UUID
    partner_id: UUID
    requested_by: Optional[UUID] = None
    status: RequestStatus = RequestStatus.PENDING

class PartnerRequestUpdate(BaseModel):
    business_id: Optional[UUID] = None
    partner_id: Optional[UUID] = None
    requested_by: Optional[UUID] = None
    status: Optional[RequestStatus] = None
    created_at: Optional[datetime] = None

class PartnerRequestResponse(PartnerRequestBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
