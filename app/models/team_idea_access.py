from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class TeamIdeaAccess(Base):
    """
    Many-to-Many mapping table between Teams and Ideas.
    Allows a team to be granted access to multiple specific ideas.
    """

    __tablename__ = "team_idea_access"

    team_id = Column(
        UUID(as_uuid = True),
        ForeignKey("teams.id", ondelete = "CASCADE"),
        primary_key = True
    )
    idea_id = Column(
        UUID(as_uuid = True),
        ForeignKey("ideas.id", ondelete = "CASCADE"),
        primary_key = True
    )
    
