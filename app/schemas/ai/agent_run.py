from app.models.enums import AgentRunStatus
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID

class AgentRunBase(BaseModel):
    stage_id: UUID
    agent_id: UUID
    input_data: Optional[dict] = None
    output_data: Optional[dict] = None
    confidence_score: Optional[float] = None
    status: AgentRunStatus = AgentRunStatus.PENDING
    execution_time_ms: Optional[int] = None

class AgentRunCreate(BaseModel):
    stage_id: UUID
    agent_id: UUID
    input_data: Optional[dict] = None
    output_data: Optional[dict] = None
    confidence_score: Optional[float] = None
    status: AgentRunStatus = AgentRunStatus.PENDING
    execution_time_ms: Optional[int] = None

class AgentRunUpdate(BaseModel):
    stage_id: Optional[UUID] = None
    agent_id: Optional[UUID] = None
    input_data: Optional[dict] = None
    output_data: Optional[dict] = None
    confidence_score: Optional[float] = None
    status: Optional[AgentRunStatus] = None
    execution_time_ms: Optional[int] = None
    created_at: Optional[datetime] = None

class AgentRunResponse(AgentRunBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
