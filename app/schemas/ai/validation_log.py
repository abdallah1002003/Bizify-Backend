from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID

class ValidationLogBase(BaseModel):
    agent_run_id: UUID
    confidence_score: float
    critique_json: Optional[dict] = None
    threshold_passed: Optional[bool] = None

class ValidationLogCreate(BaseModel):
    agent_run_id: UUID
    confidence_score: float
    critique_json: Optional[dict] = None
    threshold_passed: Optional[bool] = None

class ValidationLogUpdate(BaseModel):
    agent_run_id: Optional[UUID] = None
    confidence_score: Optional[float] = None
    critique_json: Optional[dict] = None
    threshold_passed: Optional[bool] = None
    created_at: Optional[datetime] = None

class ValidationLogResponse(ValidationLogBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
