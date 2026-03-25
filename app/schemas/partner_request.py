import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.partner_request import RequestStatus


class PartnerRequestBase(BaseModel):
    """
    Base Pydantic model for Partner Request data.
    """
    
    business_id: uuid.UUID
    partner_id: uuid.UUID
    status: Optional[RequestStatus] = RequestStatus.PENDING

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v


class PartnerRequestCreate(PartnerRequestBase):
    """
    Pydantic model for creating a Partner Request.
    """
    
    requested_by: uuid.UUID


class PartnerRequestUpdate(BaseModel):
    """
    Pydantic model for updating a Partner Request.
    """
    
    status: Optional[RequestStatus] = None

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v


class PartnerRequestRead(PartnerRequestBase):
    """
    Pydantic model for reading Partner Request data.
    """
    
    id: uuid.UUID
    requested_by: uuid.UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
