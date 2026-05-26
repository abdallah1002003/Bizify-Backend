import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.partner_profile import PartnerType
from app.models.partner_request import RequestStatus


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
