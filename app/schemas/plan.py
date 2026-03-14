from pydantic import BaseModel, ConfigDict
from uuid import UUID
from decimal import Decimal
from typing import Optional, Any

class PlanBase(BaseModel):
    name: str
    price: Decimal
    features_json: Optional[Any] = None
    is_active: Optional[bool] = True

class PlanCreate(PlanBase):
    pass

class PlanRead(PlanBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)
