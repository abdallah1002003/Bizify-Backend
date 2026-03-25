import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

class GroupRole(enum.Enum):
    OWNER = "OWNER"
    EDITOR = "EDITOR"
    VIEWER = "VIEWER"

class GroupMemberStatus(enum.Enum):
    ACTIVE = "active"
    REMOVAL_PENDING = "removal_pending"

class GroupMember(Base):
    """
    SQLAlchemy model representing a user's membership in a specific Group.
    Holds their individual role and permissions within the context of the business.
    """
    
    __tablename__ = "group_members"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    group_id = Column(UUID(as_uuid = True), ForeignKey("groups.id", ondelete="CASCADE"), nullable = False)
    user_id = Column(UUID(as_uuid = True), ForeignKey("users.id", ondelete="CASCADE"), nullable = False)
    
    role = Column(
        Enum(GroupRole, values_callable = lambda x: [e.value for e in x]), 
        default = GroupRole.VIEWER,
        nullable = False
    )
    
    status = Column(
        Enum(GroupMemberStatus, values_callable = lambda x: [e.value for e in x]), 
        default = GroupMemberStatus.ACTIVE,
        nullable = False
    )
    
    joined_at = Column(DateTime, default = lambda: datetime.now(timezone.utc))

    group = relationship("Group", back_populates = "members")
    user = relationship("User")
    
    accessible_ideas = relationship(
        "Idea", 
        secondary = "group_member_idea_access",
        viewonly = False
    )
