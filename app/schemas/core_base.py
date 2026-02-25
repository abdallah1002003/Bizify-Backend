# type: ignore
from pydantic import BaseModel, field_validator
from typing import Any
import bleach

class SafeBaseModel(BaseModel):
    """
    A base model that securely strips all HTML tags from any standard string fields,
    preventing XSS attacks automatically across all inheriting schemas.
    """
    
    @field_validator('*', mode='before')
    @classmethod
    def sanitize_strings(cls, value: Any) -> Any:
        def recursive_sanitize(val: Any) -> Any:
            if isinstance(val, str):
                return bleach.clean(val, tags=[], attributes={}, strip=True).strip()
            elif isinstance(val, dict):
                return {k: recursive_sanitize(v) for k, v in val.items()}
            elif isinstance(val, list):
                return [recursive_sanitize(item) for item in val]
            return val

        return recursive_sanitize(value)
