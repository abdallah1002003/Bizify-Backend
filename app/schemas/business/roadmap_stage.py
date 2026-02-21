from app.models.enums import RoadmapStageStatus, StageType
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID

class RoadmapStageBase(BaseModel):
    roadmap_id: UUID
    order_index: int
    stage_type: StageType
    status: RoadmapStageStatus
    output_json: Optional[dict] = None

class RoadmapStageCreate(BaseModel):
    roadmap_id: UUID
    order_index: int
    stage_type: StageType
    status: RoadmapStageStatus
    output_json: Optional[dict] = None

class RoadmapStageUpdate(BaseModel):
    roadmap_id: Optional[UUID] = None
    order_index: Optional[int] = None
    stage_type: Optional[StageType] = None
    status: Optional[RoadmapStageStatus] = None
    output_json: Optional[dict] = None
    completed_at: Optional[datetime] = None

class RoadmapStageResponse(RoadmapStageBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
