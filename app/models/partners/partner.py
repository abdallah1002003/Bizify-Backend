import uuid
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text, Enum, JSON, UniqueConstraint
from app.db.guid import GUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base
from app.models.enums import PartnerType, ApprovalStatus, RequestStatus
from app.core.crud_utils import _utc_now as utc_now

if TYPE_CHECKING:
    from app.models.users.user import User
    from app.models.business.business import Business

class PartnerProfile(Base):
    __tablename__ = "partner_profiles"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    partner_type: Mapped[PartnerType] = mapped_column(Enum(PartnerType), nullable=False)
    company_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    services_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    experience_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    approval_status: Mapped[ApprovalStatus] = mapped_column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="partner_profiles")
    approver: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by])
    partner_requests: Mapped[List["PartnerRequest"]] = relationship("PartnerRequest", foreign_keys="PartnerRequest.partner_id", back_populates="partner", cascade="all, delete-orphan")


class PartnerRequest(Base):
    __tablename__ = "partner_requests"
    ##Afnan - Added unique constraint for partner_requests
    __table_args__ = (
        UniqueConstraint("business_id", "partner_id", name="uq_partner_request_business_partner"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    partner_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("partner_profiles.id", ondelete="CASCADE"), nullable=False)
    requested_by: Mapped[Optional[uuid.UUID]] = mapped_column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[RequestStatus] = mapped_column(Enum(RequestStatus), default=RequestStatus.PENDING)
    request_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    context_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    business: Mapped["Business"] = relationship("Business", back_populates="partner_requests")
    partner: Mapped["PartnerProfile"] = relationship("PartnerProfile", foreign_keys=[partner_id], back_populates="partner_requests")
    requester: Mapped[Optional["User"]] = relationship("User", foreign_keys=[requested_by])
