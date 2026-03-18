import uuid

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class GuidanceStage(Base):
    """
    Stores the top-level stages in the business guidance system.
    """

    __tablename__ = "guidance_stages"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    name = Column(String, nullable = False)
    description = Column(Text)
    sequence_order = Column(Integer, nullable = False, unique = True)

    concepts = relationship(
        "GuidanceConcept",
        back_populates = "stage",
        order_by = "GuidanceConcept.sequence_order"
    )
