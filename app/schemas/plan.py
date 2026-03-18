import uuid
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class PlanBase(BaseModel):
    """
    Base Pydantic model for Subscription Plan data.
    """
    
    name: str
    price: Decimal
    features_json: Optional[Any] = None
    is_active: Optional[bool] = True


class PlanCreate(PlanBase):
    """
    Pydantic model for creating a new Subscription Plan.
    """
    
    pass


class PlanRead(PlanBase):
    """
    Pydantic model for reading Subscription Plan data.
    """
    
    id: uuid.UUID
    
    model_config = ConfigDict(from_attributes=True)
