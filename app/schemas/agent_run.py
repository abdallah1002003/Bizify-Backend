import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, field_validator


class AgentRunBase(BaseModel):
    """
    Base Pydantic model for Agent Run data.
    """
    
    stage_id: uuid.UUID
    agent_id: uuid.UUID
    input_data: Optional[Any] = None
    output_data: Optional[Any] = None
    confidence_score: Optional[float] = None
    execution_time_ms: Optional[int] = None

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v


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
