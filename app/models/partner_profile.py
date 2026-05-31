import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class PartnerType(str, enum.Enum):
    """
    Enumeration of different types of partners.
    """

    MENTOR = "MENTOR"
    SUPPLIER = "SUPPLIER"
    MANUFACTURER = "MANUFACTURER"


class ApprovalStatus(str, enum.Enum):
    """
    Enumeration of approval statuses for partner applications.
    """

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class PartnerProfile(Base):
    """
    SQLAlchemy model representing a Partner Profile/Application.
    """

    __tablename__ = "partner_profiles"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    user_id = Column(UUID(as_uuid = True), ForeignKey("users.id"), nullable = False)
    
    partner_type = Column(
        Enum(PartnerType, values_callable = lambda x: [e.value for e in x]), 
        nullable = False
    )
    
    company_name = Column(String)
    phone_number = Column(String, nullable=True)
    description = Column(Text)
    services_json = Column(JSON)
    experience_json = Column(JSON)
    documents_json = Column(JSON)
    
    category_id = Column(UUID(as_uuid=True), ForeignKey("partner_categories.id"), nullable=True)
    linkedin_url = Column(String, nullable=True)
    headline = Column(String, nullable=True)
    about_summary = Column(Text, nullable=True)
    skills_json = Column(JSON, nullable=True)
    country = Column(String, nullable=True)

    # ── Rich supplier/manufacturer fields (see scripts/seed_marketplace_suppliers_manufacturers.py) ──
    # Contact / web presence
    whatsapp = Column(String, nullable=True)
    email = Column(String, nullable=True)
    website = Column(String, nullable=True)
    facebook_url = Column(String, nullable=True)
    facebook_followers = Column(Integer, nullable=True)
    instagram_url = Column(String, nullable=True)
    tiktok_url = Column(String, nullable=True)
    google_maps_url = Column(String, nullable=True)
    google_rating = Column(Float, nullable=True)
    review_count = Column(Integer, nullable=True)

    # Location
    address = Column(String, nullable=True)
    area = Column(String, nullable=True)
    city = Column(String, nullable=True)
    governorate = Column(String, nullable=True)

    # Business classification
    industry = Column(String, nullable=True)
    business_model = Column(String, nullable=True)
    minimum_order_quantity = Column(String, nullable=True)
    delivery_available = Column(Boolean, nullable=True)
    estimated_size = Column(String, nullable=True)

    # Manufacturer-specific
    factory_name = Column(String, nullable=True)
    factory_address = Column(String, nullable=True)
    factory_area = Column(String, nullable=True)
    production_capacity = Column(String, nullable=True)
    private_label_available = Column(Boolean, nullable=True)
    exporting = Column(Boolean, nullable=True)
    year_founded = Column(Integer, nullable=True)
    employee_count = Column(Integer, nullable=True)

    # Provenance
    verification_score = Column(Integer, nullable=True)
    last_verified_date = Column(String, nullable=True)

    # List-valued fields (stored as JSON arrays)
    industry_tags = Column(JSON, nullable=True)
    product_tags = Column(JSON, nullable=True)
    products = Column(JSON, nullable=True)
    brands_distributed = Column(JSON, nullable=True)
    distribution_areas = Column(JSON, nullable=True)
    manufacturing_capabilities = Column(JSON, nullable=True)
    certifications = Column(JSON, nullable=True)
    export_countries = Column(JSON, nullable=True)
    source_urls = Column(JSON, nullable=True)

    approval_status = Column(
        Enum(ApprovalStatus, values_callable = lambda x: [e.value for e in x]), 
        default = ApprovalStatus.PENDING
    )
    
    approved_by = Column(UUID(as_uuid = True), ForeignKey("users.id"))
    approved_at = Column(DateTime)
    created_at = Column(DateTime, default = datetime.utcnow)

    user = relationship("User", foreign_keys = [user_id], back_populates = "partner_profile")
    approver = relationship("User", foreign_keys = [approved_by])
    requests = relationship("PartnerRequest", back_populates = "partner")
    category_ref = relationship("PartnerCategory", back_populates = "partners")
