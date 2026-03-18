import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class CollaboratorRole(str, enum.Enum):
    """
    Enumeration of specific roles assigned to business collaborators.
    """
    
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


class CollaboratorStatus(str, enum.Enum):
    """
    Enumeration of collaborator status (AF_A4).
    """
    ACTIVE = "active"
    REMOVAL_PENDING = "removal_pending"


class BusinessCollaborator(Base):
    """
    SQLAlchemy model representing a cross-reference between Users and Businesses.
    Defines the role and granular idea-level access permissions.
    """
    
    __tablename__ = "business_collaborators"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    business_id = Column(UUID(as_uuid = True), ForeignKey("businesses.id"), nullable = False)
    user_id = Column(UUID(as_uuid = True), ForeignKey("users.id"), nullable = False)
    
    role = Column(
        Enum(CollaboratorRole, values_callable = lambda x: [e.value for e in x]), 
        nullable = False
    )
    
    status = Column(
        Enum(CollaboratorStatus, values_callable = lambda x: [e.value for e in x]), 
        default = CollaboratorStatus.ACTIVE,
        nullable = False
    )
    
    # Legacy field for single-idea access
    idea_id = Column(UUID(as_uuid = True), ForeignKey("ideas.id"), nullable = True)
    
    added_at = Column(DateTime, default = datetime.utcnow)

    business = relationship("Business", back_populates = "collaborators")
    user = relationship("User")
    idea = relationship("Idea")
    
    # Granular access control for multiple ideas
    accessible_ideas = relationship(
        "Idea", 
        secondary = "collaborator_idea_access",
        viewonly = False
    )
