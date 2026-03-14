from sqlalchemy import Column, Enum, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime
import enum

class CollaboratorRole(str, enum.Enum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"

class BusinessCollaborator(Base):
    __tablename__ = "business_collaborators"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(Enum(CollaboratorRole), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="collaborators")
    user = relationship("User")
