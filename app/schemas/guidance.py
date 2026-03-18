from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class GuidanceConceptBase(BaseModel):
    """
    Base Pydantic model for guidance concept data.
    """

    title: str
    concept_explanation: str
    platform_support_explanation: Optional[str] = None
    sequence_order: int
    is_available: bool = True


class GuidanceConcept(GuidanceConceptBase):
    """
    Pydantic model representing a guidance concept.
    """

    id: UUID
    stage_id: UUID

    model_config = ConfigDict(from_attributes = True)


class GuidanceStageBase(BaseModel):
    """
    Base Pydantic model for guidance stage data.
    """

    name: str
    description: Optional[str] = None
    sequence_order: int


class GuidanceStage(GuidanceStageBase):
    """
    Pydantic model representing a guidance stage.
    """

    id: UUID
    concepts: List[GuidanceConcept] = []

    model_config = ConfigDict(from_attributes = True)


class UserConceptStateBase(BaseModel):
    """
    Base Pydantic model for user concept tracking state.
    """

    last_viewed_concept_id: UUID


class UserConceptState(UserConceptStateBase):
    """
    Pydantic model representing user concept state.
    """

    user_id: UUID
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes = True)


class FeatureConceptMappingBase(BaseModel):
    """
    Base Pydantic model for mapping features to concepts.
    """

    feature_key: str
    concept_id: UUID

    model_config = ConfigDict(from_attributes = True)
