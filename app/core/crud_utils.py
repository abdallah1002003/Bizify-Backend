"""
Utilities for CRUD operations and data transformation.

This module provides helper functions for:
    - Working with UTC timestamps consistently
    - Converting Pydantic schemas to dictionaries for database operations
    - Applying updates to ORM objects
    - Handling both Pydantic models and plain dictionaries

These utilities are used throughout the service layer for consistent data handling.
"""

from datetime import datetime, timezone
from typing import Any, Dict, cast


def _utc_now() -> datetime:
    """
    Get the current time in UTC timezone.
    
    Returns a timezone-aware datetime object in UTC, suitable for
    storing in database timestamp fields.
    
    Returns:
        datetime: Current UTC time with timezone info
        
    Example:
        >>> now = _utc_now()
        >>> user.created_at = now
        >>> user.updated_at = now
        
    Note:
        - Always returns UTC time (timezone.utc)
        - Safe for database storage without additional conversion
        - Timezone-aware, so comparisons work correctly across regions
    """
    return datetime.now(timezone.utc)


def _to_update_dict(obj_in: Any) -> Dict[str, Any]:
    """
    Convert input object to a dictionary for database updates.
    
    Handles multiple input types intelligently:
    - Pydantic BaseModel: Uses model_dump(exclude_unset=True) to only include set fields
    - Dictionary: Returns as-is
    - Other objects: Attempts dict() conversion
    - None: Returns empty dictionary
    
    Args:
        obj_in: Input object (Pydantic model, dict, or other)
    
    Returns:
        Dict[str, Any]: Flattened dictionary suitable for database operations
        
    Example:
        >>> from pydantic import BaseModel
        >>> class UserUpdate(BaseModel):
        ...     name: str = None
        ...     email: str = None
        >>> data = UserUpdate(name="John")
        >>> update_dict = _to_update_dict(data)
        >>> # Result: {"name": "John"} (email not included as unset)
        
    Note:
        - Pydantic models exclude unset fields (exclude_unset=True)
        - This prevents unintended None overwrites in partial updates
        - Returns empty dict for None input (safe behavior)
    """
    if obj_in is None:
        return {}
    if hasattr(obj_in, "model_dump"):
        return cast(Dict[str, Any], obj_in.model_dump(exclude_unset=True))
    return cast(Dict[str, Any], dict(obj_in))


def _apply_updates(db_obj: Any, update_data: Dict[str, Any]) -> Any:
    """
    Apply dictionary of updates to a SQLAlchemy ORM object.
    
    Iterates through update_data and sets matching attributes on db_obj.
    Only updates attributes that exist on the object (safe for mismatched fields).
    
    Args:
        db_obj: SQLAlchemy model instance to update
        update_data: Dictionary of field_name: value pairs to apply
    
    Returns:
        The updated ORM object (same instance, modified in-place)
        
    Example:
        >>> user = db.query(User).filter(User.id == user_id).first()
        >>> updates = {"name": "John Doe", "bio": "Developer"}
        >>> user = _apply_updates(user, updates)
        >>> db.commit()
        
    Note:
        - Modifies the object in-place
        - Only sets attributes that exist with hasattr check
        - Ignores fields in update_data that don't exist on model
        - Caller is responsible for db.commit() or db.flush()
    """
    for field, value in update_data.items():
        if hasattr(db_obj, field):
            setattr(db_obj, field, value)
    return cast(Any, db_obj)
