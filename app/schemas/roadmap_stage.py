from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, Any
from app.models.roadmap_stage import StageType, StageStatus

class RoadmapStageBase(BaseModel):
    roadmap_id: UUID
    order_index: int
    stage_type: StageType
    status: Optional[StageStatus] = StageStatus.LOCKED
    output_json: Optional[Any] = None

class RoadmapStageCreate(RoadmapStageBase):
    pass

class RoadmapStageUpdate(BaseModel):
    order_index: Optional[int] = None
    stage_type: Optional[StageType] = None
    status: Optional[StageStatus] = None
    output_json: Optional[Any] = None
    completed_at: Optional[datetime] = None

class RoadmapStageRead(RoadmapStageBase):
    id: UUID
    completed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
