import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.business_collaborator import CollaboratorRole


class JoinRequestStatus(str, enum.Enum):
    """
    Enumeration of lifecycle statuses for a business join request.
    """
    
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class BusinessJoinRequest(Base):
    """
    SQLAlchemy model representing an external user's request to join a business team.
    Captures intended role and requested idea access for owner review.
    """
    
    __tablename__ = "business_join_requests"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    business_id = Column(UUID(as_uuid = True), ForeignKey("businesses.id"), nullable = False)
    user_id = Column(UUID(as_uuid = True), ForeignKey("users.id"), nullable = False)
    
    status = Column(
        Enum(JoinRequestStatus, values_callable = lambda x: [e.value for e in x]), 
        default = JoinRequestStatus.PENDING
    )
    
    role = Column(
        Enum(CollaboratorRole, values_callable = lambda x: [e.value for e in x]), 
        nullable = False, 
        default = CollaboratorRole.VIEWER
    )
    
    created_at = Column(DateTime, default = datetime.utcnow)
    updated_at = Column(DateTime, default = datetime.utcnow, onupdate = datetime.utcnow)

    # Granular idea access requested by the user or proposed by the invite
    accessible_ideas = relationship(
        "Idea", 
        secondary = "join_request_idea_access", 
        backref = "associated_requests"
    )

    business = relationship("Business")
    user = relationship("User")
