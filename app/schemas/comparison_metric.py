from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional

class ComparisonMetricBase(BaseModel):
    comparison_id: UUID
    metric_name: str
    value: Optional[float] = None

class ComparisonMetricRead(ComparisonMetricBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)
