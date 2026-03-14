from sqlalchemy import Column, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime

class BusinessRoadmap(Base):
    __tablename__ = "business_roadmaps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False)
    completion_percentage = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="roadmap")
    stages = relationship("RoadmapStage", back_populates="roadmap", order_by="RoadmapStage.order_index")
