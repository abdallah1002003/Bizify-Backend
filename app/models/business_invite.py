import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.business_collaborator import CollaboratorRole


class InviteStatus(str, enum.Enum):
    """
    Enumeration of lifecycle statuses for a business invitation.
    """
    
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"


class BusinessInvite(Base):
    """
    SQLAlchemy model representing an invitation to join a business team.
    Stores pre-defined roles and idea-level permissions before the user accepts.
    """
    
    __tablename__ = "business_invites"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    business_id = Column(UUID(as_uuid = True), ForeignKey("businesses.id"), nullable = False)
    email = Column(String, nullable = True)
    token = Column(String, unique = True, nullable = False)
    
    status = Column(
        Enum(InviteStatus, values_callable = lambda x: [e.value for e in x]), 
        default = InviteStatus.PENDING
    )
    
    invited_by = Column(UUID(as_uuid = True), ForeignKey("users.id"), nullable = False)
    expires_at = Column(DateTime, nullable = False)
    created_at = Column(DateTime, default = datetime.utcnow)
    
    role = Column(
        Enum(CollaboratorRole, values_callable = lambda x: [e.value for e in x]), 
        nullable = False, 
        default = CollaboratorRole.VIEWER
    )
    
    requires_approval = Column(Boolean, default = True)
    
    # Granular access control applied upon acceptance
    accessible_ideas = relationship(
        "Idea", 
        secondary = "invite_idea_access", 
        backref = "associated_invites"
    )

    business = relationship("Business", back_populates = "invites")
    inviter = relationship("User")
