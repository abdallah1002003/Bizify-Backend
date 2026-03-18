import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ComparisonMetricBase(BaseModel):
    """
    Base Pydantic model for Comparison Metric data.
    """
    
    comparison_id: uuid.UUID
    metric_name: str
    value: Optional[float] = None


class ComparisonMetricRead(ComparisonMetricBase):
    """
    Pydantic model for reading Comparison Metric data.
    """
    
    id: uuid.UUID
    
    model_config = ConfigDict(from_attributes=True)
