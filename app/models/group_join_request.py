import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.group_member import GroupRole

class GroupJoinRequestStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class GroupJoinRequest(Base):
    """
    SQLAlchemy model representing a request from an internal user to join a Group.
    If approved, the owner assigns them a role and accessible ideas.
    Wait, the user is requesting access to a specific group, and they can request a specific role/ideas
    or the owner sets it post-approval. Let's keep role here so if they request it, they can ask for it.
    """
    
    __tablename__ = "group_join_requests"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    group_id = Column(UUID(as_uuid = True), ForeignKey("groups.id", ondelete="CASCADE"), nullable = False)
    user_id = Column(UUID(as_uuid = True), ForeignKey("users.id", ondelete="CASCADE"), nullable = False)
    
    role = Column(
        Enum(GroupRole, values_callable = lambda x: [e.value for e in x]), 
        default = GroupRole.VIEWER,
        nullable = False
    )

    status = Column(
        Enum(GroupJoinRequestStatus, values_callable = lambda x: [e.value for e in x]), 
        default = GroupJoinRequestStatus.PENDING
    )
    
    created_at = Column(DateTime, default = lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default = lambda: datetime.now(timezone.utc), onupdate = lambda: datetime.now(timezone.utc))

    group = relationship("Group", back_populates = "join_requests")
    user = relationship("User")
    
    accessible_ideas = relationship(
        "Idea", 
        secondary = "group_request_idea_access",
        viewonly = False
    )
