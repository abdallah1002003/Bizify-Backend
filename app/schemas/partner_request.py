from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.models.partner_request import RequestStatus

class PartnerRequestBase(BaseModel):
    business_id: UUID
    partner_id: UUID
    status: Optional[RequestStatus] = RequestStatus.PENDING

class PartnerRequestCreate(PartnerRequestBase):
    requested_by: UUID

class PartnerRequestUpdate(BaseModel):
    status: Optional[RequestStatus] = None

class PartnerRequestRead(PartnerRequestBase):
    id: UUID
    requested_by: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
