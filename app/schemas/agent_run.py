import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.ai.agent_run import AgentAIType, RunStatus


class AgentRunBase(BaseModel):
    """
    Base Pydantic model for Agent Run data.
    """
    
    ai_type: AgentAIType = AgentAIType.ROADMAP_STAGE
    roadmap_id: Optional[uuid.UUID] = None
    stage_id: Optional[uuid.UUID] = None
    chat_session_id: Optional[uuid.UUID] = None
    chat_message_id: Optional[uuid.UUID] = None
    idea_id: Optional[uuid.UUID] = None
    idea_metric_id: Optional[uuid.UUID] = None
    idea_comparison_id: Optional[uuid.UUID] = None
    comparison_item_id: Optional[uuid.UUID] = None
    comparison_metric_id: Optional[uuid.UUID] = None
    experiment_id: Optional[uuid.UUID] = None
    agent_id: Optional[uuid.UUID] = None
    input_data: Optional[Any] = None
    output_data: Optional[Any] = None
    confidence_score: Optional[float] = None
    status: Optional[RunStatus] = None
    execution_time_ms: Optional[int] = None
    critique_json: Optional[Any] = None
    threshold_passed: Optional[bool] = None

    @field_validator("ai_type", "status", mode="before")
    @classmethod
    def validate_enums(cls, v):
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
