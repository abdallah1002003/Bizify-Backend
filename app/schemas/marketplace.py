import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.partner_profile import PartnerType
from app.models.partner_request import RequestStatus


class PartnerCategoryRead(BaseModel):
    id: uuid.UUID
    name: str
    partner_type: PartnerType

    model_config = ConfigDict(from_attributes=True)


class MarketplacePartnerPublic(BaseModel):
    """Approved partner card shown in marketplace listings (no internal documents)."""

    id: uuid.UUID
    partner_type: PartnerType
    company_name: Optional[str] = None
    phone_number: Optional[str] = None
    description: Optional[str] = None
    services_json: Optional[Any] = None
    experience_json: Optional[Any] = None
    display_name: Optional[str] = None
    category_id: Optional[uuid.UUID] = None
    category_name: Optional[str] = None
    linkedin_url: Optional[str] = None
    headline: Optional[str] = None
    about_summary: Optional[str] = None
    skills_json: Optional[Any] = None
    country: Optional[str] = None
    documents_json: Optional[Any] = None

    model_config = ConfigDict(from_attributes=True)


class MarketplacePartnerRequestCreate(BaseModel):
    """Body for submitting a collaboration request to a marketplace partner."""

    business_id: uuid.UUID = Field(..., description="Business owned by the current user")


class MarketplacePartnerRequestRead(BaseModel):
    """A collaboration request with linked partner summary for the requester."""

    id: uuid.UUID
    business_id: uuid.UUID
    partner_id: uuid.UUID
    requested_by: uuid.UUID
    status: RequestStatus
    created_at: datetime
    partner: Optional[MarketplacePartnerPublic] = None

    model_config = ConfigDict(from_attributes=True)
