import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class ValidationLogBase(BaseModel):
    """
    Base Pydantic model for Validation Log data.
    """
    
    agent_run_id: uuid.UUID
    confidence_score: Optional[float] = None
    critique_json: Optional[Any] = None
    threshold_passed: Optional[bool] = None


class ValidationLogCreate(ValidationLogBase):
    """
    Pydantic model for creating a new Validation Log.
    """
    
    pass


class ValidationLogRead(ValidationLogBase):
    """
    Pydantic model for reading Validation Log data.
    """
    
    id: uuid.UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
