import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class TeamMember(Base):
    """
    SQLAlchemy model representing a cross-reference between Teams and Users.
    """
    
    __tablename__ = "team_members"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    team_id = Column(UUID(as_uuid = True), ForeignKey("teams.id", ondelete="CASCADE"), nullable = False)
    user_id = Column(UUID(as_uuid = True), ForeignKey("users.id", ondelete="CASCADE"), nullable = False)
    
    added_at = Column(DateTime, default = datetime.utcnow)

    team = relationship("Team", back_populates = "members")
    user = relationship("User")
