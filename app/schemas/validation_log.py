from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, Any

class ValidationLogBase(BaseModel):
    agent_run_id: UUID
    confidence_score: Optional[float] = None
    critique_json: Optional[Any] = None
    threshold_passed: Optional[bool] = None

class ValidationLogCreate(ValidationLogBase):
    pass

class ValidationLogRead(ValidationLogBase):
    id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
