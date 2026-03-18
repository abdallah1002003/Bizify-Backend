import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ExperimentBase(BaseModel):
    """
    Base Pydantic model for Experiment data.
    """
    
    hypothesis: str
    status: Optional[str] = None
    result_summary: Optional[str] = None


class ExperimentCreate(ExperimentBase):
    """
    Pydantic model for creating a new Experiment.
    """
    
    idea_id: uuid.UUID
    created_by: uuid.UUID


class ExperimentRead(ExperimentBase):
    """
    Pydantic model for reading Experiment data.
    """
    
    id: uuid.UUID
    idea_id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
