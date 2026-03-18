import uuid

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class CollaboratorIdeaAccess(Base):
    """
    Many-to-Many mapping table between BusinessCollaborators and Ideas.
    Allows a collaborator to have access to multiple specific ideas.
    """

    __tablename__ = "collaborator_idea_access"

    collaborator_id = Column(
        UUID(as_uuid = True),
        ForeignKey("business_collaborators.id", ondelete = "CASCADE"),
        primary_key = True
    )
    idea_id = Column(
        UUID(as_uuid = True),
        ForeignKey("ideas.id", ondelete = "CASCADE"),
        primary_key = True
    )
