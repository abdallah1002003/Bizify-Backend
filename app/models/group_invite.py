import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.group_member import GroupRole

class GroupInviteStatus(enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    EXPIRED = "EXPIRED"

class GroupInvite(Base):
    """
    SQLAlchemy model representing an invitation to join a Group.
    Holds the temporary token and the role/ideas the user will receive upon accepting.
    """
    __tablename__ = "group_invites"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    group_id = Column(UUID(as_uuid = True), ForeignKey("groups.id", ondelete="CASCADE"), nullable = False)
    
    email = Column(String, nullable = True)
    token = Column(String, unique = True, nullable = False)
    
    role = Column(
        Enum(GroupRole, values_callable = lambda x: [e.value for e in x]), 
        default = GroupRole.VIEWER,
        nullable = False
    )
    
    status = Column(
        Enum(GroupInviteStatus, values_callable = lambda x: [e.value for e in x]), 
        default = GroupInviteStatus.PENDING
    )
    
    invited_by = Column(UUID(as_uuid = True), ForeignKey("users.id"), nullable = False)
    expires_at = Column(DateTime, nullable = False)
    created_at = Column(DateTime, default = lambda: datetime.now(timezone.utc))

    group = relationship("Group", back_populates = "invites")
    inviter = relationship("User")
    
    accessible_ideas = relationship(
        "Idea", 
        secondary = "group_invite_idea_access",
        viewonly = False
    )
