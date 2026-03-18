import uuid

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class GuidanceConcept(Base):
    """
    Stores detailed business concepts associated with each guidance stage.
    """

    __tablename__ = "guidance_concepts"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    stage_id = Column(UUID(as_uuid = True), ForeignKey("guidance_stages.id"), nullable = False)
    title = Column(String, nullable = False)
    concept_explanation = Column(Text, nullable = False)
    platform_support_explanation = Column(Text)
    sequence_order = Column(Integer, nullable = False)
    is_available = Column(Boolean, default = True)

    stage = relationship("GuidanceStage", back_populates = "concepts")
