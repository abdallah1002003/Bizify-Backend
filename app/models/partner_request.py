import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class RequestStatus(str, enum.Enum):
    """
    Enumeration of statuses for a partner request.
    """

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class PartnerRequest(Base):
    """
    SQLAlchemy model representing a request to collaborate with a Partner.
    """

    __tablename__ = "partner_requests"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    business_id = Column(UUID(as_uuid = True), ForeignKey("businesses.id"), nullable = False)
    partner_id = Column(
        UUID(as_uuid = True),
        ForeignKey("partner_profiles.id"),
        nullable = False
    )
    requested_by = Column(UUID(as_uuid = True), ForeignKey("users.id"), nullable = False)
    status = Column(
        Enum(RequestStatus, values_callable = lambda x: [e.value for e in x]),
        default = RequestStatus.PENDING
    )
    created_at = Column(DateTime, default = datetime.utcnow)

    business = relationship("Business", back_populates = "partner_requests")
    partner = relationship("PartnerProfile", back_populates = "requests")
    requester = relationship("User")
