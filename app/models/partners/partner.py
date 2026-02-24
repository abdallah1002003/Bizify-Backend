import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum, JSON
from app.db.guid import GUID
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.models.enums import PartnerType, ApprovalStatus, RequestStatus
from app.core.crud_utils import _utc_now as utc_now

class PartnerProfile(Base):
    __tablename__ = "partner_profiles"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    partner_type: Column[PartnerType] = Column(Enum(PartnerType), nullable=False)
    company_name = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    services_json = Column(JSON, nullable=True)
    experience_json = Column(JSON, nullable=True)
    approval_status: Column[ApprovalStatus] = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    approved_by = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    user = relationship("User", foreign_keys=[user_id], back_populates="partner_profiles")
    approver = relationship("User", foreign_keys=[approved_by])
    partner_requests = relationship("PartnerRequest", foreign_keys="PartnerRequest.partner_id", back_populates="partner", cascade="all, delete-orphan")


class PartnerRequest(Base):
    __tablename__ = "partner_requests"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    business_id = Column(GUID, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    partner_id = Column(GUID, ForeignKey("partner_profiles.id", ondelete="CASCADE"), nullable=False)
    requested_by = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Column[RequestStatus] = Column(Enum(RequestStatus), default=RequestStatus.PENDING)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    business = relationship("Business", back_populates="partner_requests")
    partner = relationship("PartnerProfile", foreign_keys=[partner_id], back_populates="partner_requests")
    requester = relationship("User", foreign_keys=[requested_by])
