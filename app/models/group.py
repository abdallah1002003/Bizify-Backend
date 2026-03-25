import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.group_member import GroupRole

class Group(Base):
    """
    SQLAlchemy model representing an organizational Group within a Business.
    All members must belong to a Group.
    """
    
    __tablename__ = "groups"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    business_id = Column(UUID(as_uuid = True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable = False)
    
    name = Column(String(255), nullable = False)
    description = Column(String, nullable = True)
    
    default_role = Column(
        Enum(GroupRole, values_callable = lambda x: [e.value for e in x]), 
        default = GroupRole.VIEWER,
        nullable = False
    )
    
    is_chat_enabled = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, default = lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default = lambda: datetime.now(timezone.utc), onupdate = lambda: datetime.now(timezone.utc))

    business = relationship("Business")
    members = relationship("GroupMember", back_populates = "group", cascade="all, delete-orphan")
    invites = relationship("GroupInvite", back_populates = "group", cascade="all, delete-orphan")
    join_requests = relationship("GroupJoinRequest", back_populates = "group", cascade="all, delete-orphan")
    messages = relationship("GroupMessage", back_populates = "group", cascade="all, delete-orphan")
