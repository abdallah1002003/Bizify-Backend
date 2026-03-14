from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class IdeaMetricBase(BaseModel):
    name: str
    value: float
    type: Optional[str] = None

class IdeaMetricCreate(IdeaMetricBase):
    idea_id: UUID
    created_by: UUID

class IdeaMetricRead(IdeaMetricBase):
    id: UUID
    idea_id: UUID
    created_by: UUID
    recorded_at: datetime
    model_config = ConfigDict(from_attributes=True)
