import uuid

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class InviteIdeaAccess(Base):
    """
    Many-to-Many mapping table between BusinessInvites and Ideas.
    An invitation link can carry access permissions for multiple specific ideas.
    """

    __tablename__ = "invite_idea_access"

    invite_id = Column(
        UUID(as_uuid = True),
        ForeignKey("business_invites.id", ondelete = "CASCADE"),
        primary_key = True
    )
    idea_id = Column(
        UUID(as_uuid = True),
        ForeignKey("ideas.id", ondelete = "CASCADE"),
        primary_key = True
    )
