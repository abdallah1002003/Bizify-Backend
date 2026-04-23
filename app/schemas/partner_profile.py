import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.partner_profile import ApprovalStatus, PartnerType


class PartnerProfileBase(BaseModel):
    """
    Base Pydantic model for Partner Profile data.
    """
    
    partner_type: PartnerType

    @field_validator("partner_type", mode="before")
    @classmethod
    def validate_partner_type(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v
    company_name: Optional[str] = None
    description: Optional[str] = None
    services_json: Optional[Any] = None
    experience_json: Optional[Any] = None


class PartnerProfileCreate(PartnerProfileBase):
    """
    Pydantic model for creating a Partner Profile.
    """
    
    user_id: uuid.UUID


class PartnerProfileRegistration(PartnerProfileBase):
    """
    Partner profile payload collected during user registration.
    """


class PartnerProfileUpdate(BaseModel):
    """
    Pydantic model for updating a Partner Profile.
    """
    
    partner_type: Optional[PartnerType] = None
    company_name: Optional[str] = None
    description: Optional[str] = None
    services_json: Optional[Any] = None
    experience_json: Optional[Any] = None
    approval_status: Optional[ApprovalStatus] = None

    @field_validator("partner_type", "approval_status", mode="before")
    @classmethod
    def validate_enums(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v


class PartnerProfileRead(PartnerProfileBase):
    """
    Pydantic model for reading Partner Profile data.
    """
    
    id: uuid.UUID
    user_id: uuid.UUID
    approval_status: ApprovalStatus
    approved_by: Optional[uuid.UUID] = None
    documents_json: Optional[Any] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
