import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.business_collaborator import CollaboratorRole


class Team(Base):
    """
    SQLAlchemy model representing a Team (Group) within a Business.
    Allows for Group-based Access Control.
    """
    
    __tablename__ = "teams"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    business_id = Column(UUID(as_uuid = True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable = False)
    
    name = Column(String(255), nullable = False)
    description = Column(String, nullable = True)
    
    role = Column(
        Enum(CollaboratorRole, values_callable = lambda x: [e.value for e in x]), 
        default = CollaboratorRole.VIEWER,
        nullable = False
    )
    
    created_at = Column(DateTime, default = datetime.utcnow)
    updated_at = Column(DateTime, default = datetime.utcnow, onupdate = datetime.utcnow)

    business = relationship("Business")
    members = relationship("TeamMember", back_populates = "team", cascade="all, delete-orphan")
    
    accessible_ideas = relationship(
        "Idea", 
        secondary = "team_idea_access",
        viewonly = False
    )
