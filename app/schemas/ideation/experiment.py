from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any
from uuid import UUID

class ExperimentBase(BaseModel):
    idea_id: UUID
    created_by: UUID
    hypothesis: str
    status: str
    result_summary: Optional[Dict[str, Any]] = None

class ExperimentCreate(BaseModel):
    idea_id: UUID
    created_by: UUID
    hypothesis: str = Field(..., max_length=255)
    status: str = Field(..., max_length=255)
    result_summary: Optional[Dict[str, Any]] = None

class ExperimentUpdate(BaseModel):
    idea_id: Optional[UUID] = None
    created_by: Optional[UUID] = None
    hypothesis: Optional[str] = None
    status: Optional[str] = None
    result_summary: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

class ExperimentResponse(ExperimentBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
