from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, Any, Dict
from uuid import UUID

class PlanBase(BaseModel):
    name: str
    price: Decimal
    features_json: Optional[dict] = None
    is_active: Optional[bool] = None
    stripe_price_id: Optional[str] = None
    billing_cycle: Optional[str] = "month"

class PlanCreate(BaseModel):
    name: str = Field(..., max_length=255)
    price: Decimal
    features_json: Optional[dict] = None
    is_active: Optional[bool] = None
    stripe_price_id: Optional[str] = None
    billing_cycle: Optional[str] = "month"
    
    @field_validator('features_json', mode='before')
    @classmethod
    def validate_features_json(cls, v: Any) -> Dict[str, Any]:
        """Validate features_json at input time."""
        if v is None:
            return {}
        if not isinstance(v, dict):
            raise ValueError(f"features_json must be a dictionary, got {type(v).__name__}")
        try:
            import json
            json.dumps(v)
        except (TypeError, ValueError) as e:
            raise ValueError(f"features_json contains non-serializable values: {e}") from e
        return v

class PlanUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[Decimal] = None
    features_json: Optional[dict] = None
    is_active: Optional[bool] = None
    stripe_price_id: Optional[str] = None
    billing_cycle: Optional[str] = None
    
    @field_validator('features_json', mode='before')
    @classmethod
    def validate_features_json(cls, v: Any) -> Optional[Dict[str, Any]]:
        """Validate features_json at input time."""
        if v is None:
            return None
        if not isinstance(v, dict):
            raise ValueError(f"features_json must be a dictionary, got {type(v).__name__}")
        try:
            import json
            json.dumps(v)
        except (TypeError, ValueError) as e:
            raise ValueError(f"features_json contains non-serializable values: {e}") from e
        return v

class PlanResponse(PlanBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
