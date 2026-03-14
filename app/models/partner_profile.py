from sqlalchemy import Column, String, Text, JSON, Enum, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime
import enum

class PartnerType(str, enum.Enum):
    MENTOR = "mentor"
    SUPPLIER = "supplier"
    MANUFACTURER = "manufacturer"

class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class PartnerProfile(Base):
    __tablename__ = "partner_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    partner_type = Column(Enum(PartnerType), nullable=False)
    company_name = Column(String)
    description = Column(Text)
    services_json = Column(JSON)
    experience_json = Column(JSON)
    approval_status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id], back_populates="partner_profile")
    approver = relationship("User", foreign_keys=[approved_by])
    requests = relationship("PartnerRequest", back_populates="partner")
