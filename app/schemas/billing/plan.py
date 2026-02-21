from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID

class PlanBase(BaseModel):
    name: str
    price: float
    features_json: Optional[dict] = None
    is_active: Optional[bool] = None

class PlanCreate(BaseModel):
    name: str = Field(..., max_length=255)
    price: float
    features_json: Optional[dict] = None
    is_active: Optional[bool] = None

class PlanUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    features_json: Optional[dict] = None
    is_active: Optional[bool] = None

class PlanResponse(PlanBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
