import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

from app.models.agent_run import RunStatus


class AgentRunBase(BaseModel):
    """
    Base Pydantic model for Agent Run data.
    """
    
    stage_id: uuid.UUID
    agent_id: uuid.UUID
    input_data: Optional[Any] = None
    output_data: Optional[Any] = None
    confidence_score: Optional[float] = None
    status: Optional[RunStatus] = None
    execution_time_ms: Optional[int] = None


class AgentRunCreate(AgentRunBase):
    """
    Pydantic model for creating a new Agent Run.
    """
    
    pass


class AgentRunRead(AgentRunBase):
    """
    Pydantic model for reading Agent Run data.
    """
    
    id: uuid.UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
