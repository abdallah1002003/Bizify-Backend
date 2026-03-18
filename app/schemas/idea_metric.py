import uuid

from pydantic import BaseModel, ConfigDict


class IdeaMetricBase(BaseModel):
    """
    Base Pydantic model for Idea Metric data.
    """

    idea_id: uuid.UUID
    metric_name: str
    value: float


class IdeaMetricRead(IdeaMetricBase):
    """
    Pydantic model for reading Idea Metric data.
    """

    id: uuid.UUID

    model_config = ConfigDict(from_attributes = True)
