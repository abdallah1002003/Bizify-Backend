from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, Any
from app.models.agent_run import RunStatus

class AgentRunBase(BaseModel):
    stage_id: UUID
    agent_id: UUID
    input_data: Optional[Any] = None
    output_data: Optional[Any] = None
    confidence_score: Optional[float] = None
    status: Optional[RunStatus] = None
    execution_time_ms: Optional[int] = None

class AgentRunCreate(AgentRunBase):
    pass

class AgentRunRead(AgentRunBase):
    id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
