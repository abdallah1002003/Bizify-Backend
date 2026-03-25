import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.roadmap_stage import StageStatus, StageType


class RoadmapStageBase(BaseModel):
    """
    Base Pydantic model for Roadmap Stage data.
    """
    
    roadmap_id: uuid.UUID
    order_index: int
    stage_type: StageType
    status: Optional[StageStatus] = StageStatus.LOCKED
    output_json: Optional[Any] = None

    @field_validator("stage_type", "status", mode="before")
    @classmethod
    def validate_enums(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v


class RoadmapStageCreate(RoadmapStageBase):
    """
    Pydantic model for creating a new Roadmap Stage.
    """
    
    pass


class RoadmapStageUpdate(BaseModel):
    """
    Pydantic model for updating an existing Roadmap Stage.
    """
    
    order_index: Optional[int] = None
    stage_type: Optional[StageType] = None
    status: Optional[StageStatus] = None
    output_json: Optional[Any] = None
    completed_at: Optional[datetime] = None

    @field_validator("stage_type", "status", mode="before")
    @classmethod
    def validate_enums(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v


class RoadmapStageRead(RoadmapStageBase):
    """
    Pydantic model for reading Roadmap Stage data.
    """
    
    id: uuid.UUID
    completed_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
