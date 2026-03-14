from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class ExperimentBase(BaseModel):
    hypothesis: str
    status: Optional[str] = None
    result_summary: Optional[str] = None

class ExperimentCreate(ExperimentBase):
    idea_id: UUID
    created_by: UUID

class ExperimentRead(ExperimentBase):
    id: UUID
    idea_id: UUID
    created_by: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
