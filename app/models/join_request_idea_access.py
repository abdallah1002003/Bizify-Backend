import uuid

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class JoinRequestIdeaAccess(Base):
    """
    Many-to-Many mapping table between BusinessJoinRequests and Ideas.
    A join request can specify multiple ideas the user is requesting access to.
    """

    __tablename__ = "join_request_idea_access"

    request_id = Column(
        UUID(as_uuid = True),
        ForeignKey("business_join_requests.id", ondelete = "CASCADE"),
        primary_key = True
    )
    idea_id = Column(
        UUID(as_uuid = True),
        ForeignKey("ideas.id", ondelete = "CASCADE"),
        primary_key = True
    )
