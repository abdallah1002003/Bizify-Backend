import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, JSON, String, Text
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
    description = Column(Text)
    services_json = Column(JSON)
    experience_json = Column(JSON)
    documents_json = Column(JSON)
    
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
