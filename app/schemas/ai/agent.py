from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID

class AgentBase(BaseModel):
    name: str
    phase: str

class AgentCreate(BaseModel):
    name: str = Field(..., max_length=255)
    phase: str = Field(..., max_length=255)

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    phase: Optional[str] = None

class AgentResponse(AgentBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
