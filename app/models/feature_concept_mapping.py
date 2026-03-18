import uuid

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class FeatureConceptMapping(Base):
    """
    Maps platform feature keys to specific guidance concepts.
    Allows contextual guidance to be surfaced from any part of the UI.
    """

    __tablename__ = "feature_concept_mappings"

    feature_key = Column(String, primary_key = True)
    concept_id = Column(UUID(as_uuid = True), ForeignKey("guidance_concepts.id"), nullable = False)
