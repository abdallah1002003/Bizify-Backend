from sqlalchemy import Column, String, ForeignKey, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime
import enum
from app.models.business_collaborator import CollaboratorRole

class InviteStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"

class BusinessInvite(Base):
    __tablename__ = "business_invites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False)
    email = Column(String, nullable=False)
    token = Column(String, unique=True, nullable=False)
    status = Column(Enum(InviteStatus), default=InviteStatus.PENDING)
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    role = Column(Enum(CollaboratorRole), nullable=False, default=CollaboratorRole.VIEWER)
    email = Column(String, nullable=True) 

    business = relationship("Business", back_populates="invites")
    inviter = relationship("User")
