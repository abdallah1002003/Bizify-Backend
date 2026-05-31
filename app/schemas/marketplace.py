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

    # ── Rich supplier/manufacturer fields ──
    whatsapp: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    facebook_url: Optional[str] = None
    facebook_followers: Optional[int] = None
    instagram_url: Optional[str] = None
    tiktok_url: Optional[str] = None
    google_maps_url: Optional[str] = None
    google_rating: Optional[float] = None
    review_count: Optional[int] = None

    address: Optional[str] = None
    area: Optional[str] = None
    city: Optional[str] = None
    governorate: Optional[str] = None

    industry: Optional[str] = None
    business_model: Optional[str] = None
    minimum_order_quantity: Optional[str] = None
    delivery_available: Optional[bool] = None
    estimated_size: Optional[str] = None

    factory_name: Optional[str] = None
    factory_address: Optional[str] = None
    factory_area: Optional[str] = None
    production_capacity: Optional[str] = None
    private_label_available: Optional[bool] = None
    exporting: Optional[bool] = None
    year_founded: Optional[int] = None
    employee_count: Optional[int] = None

    verification_score: Optional[int] = None
    last_verified_date: Optional[str] = None

    industry_tags: Optional[Any] = None
    product_tags: Optional[Any] = None
    products: Optional[Any] = None
    brands_distributed: Optional[Any] = None
    distribution_areas: Optional[Any] = None
    manufacturing_capabilities: Optional[Any] = None
    certifications: Optional[Any] = None
    export_countries: Optional[Any] = None
    source_urls: Optional[Any] = None

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
