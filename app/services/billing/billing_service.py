"""
Usage management and quota enforcement for the billing system.

This module handles:
    - Usage quota checking and enforcement
    - Usage recording and tracking
    - Resource consumption limits
    - User quota validation

Refactored to focus on usage operations. Payment operations moved to
payment_operations.py for better code organization.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Usage
from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates

logger = logging.getLogger(__name__)


# ----------------------------
# Usage enforcement
# ----------------------------

def check_usage_limit(db: Session, user_id: UUID, resource_type: str) -> bool:
    """
    Check if a user has remaining quota for a resource.
    
    Verifies that the user's usage hasn't exceeded the limit for
    a specific resource type (e.g., AI_REQUEST).
    
    Args:
        db: Database session
        user_id: UUID of the user to check
        resource_type: Type of resource (e.g., 'AI_REQUEST', 'API_CALLS')
    
    Returns:
        True if user has remaining quota or no limit set,
        False if usage limit exceeded
        
    Example:
        >>> has_quota = check_usage_limit(db, user_id, "AI_REQUEST")
        >>> if has_quota:
        ...     # Proceed with AI request
        ... else:
        ...     # Return 429 Too Many Requests
        
    Note:
        - Returns True if no Usage record exists (no limit)
        - Returns True if limit_value is None (unlimited)
        - Thread-safe for concurrent checking
    """
    usage = (
        db.query(Usage)
        .filter(Usage.user_id == user_id, Usage.resource_type == resource_type)
        .first()
    )
    if usage is None or usage.limit_value is None:
        return True
    return usage.used < usage.limit_value


def record_usage(db: Session, user_id: UUID, resource_type: str, quantity: int = 1) -> Usage:
    """
    Record resource usage for a user.
    
    Increments the usage counter for a resource type. Uses row-level locking
    to prevent race conditions in concurrent scenarios.
    
    Args:
        db: Database session
        user_id: UUID of the user
        resource_type: Type of resource (e.g., 'AI_REQUEST')
        quantity: Quantity to add (default: 1)
    
    Returns:
        Updated Usage record with incremented counter
        
    Raises:
        SQLAlchemyError: If database operations fail
        
    Example:
        >>> usage = record_usage(db, user_id, "AI_REQUEST", quantity=1)
        >>> print(f"User has used {usage.used}/{usage.limit_value} AI requests")
        
    Note:
        - Uses FOR UPDATE locking to prevent concurrent modification issues
        - Creates new Usage record if none exists
        - Automatically commits changes
    """
    # Use row-level locking to prevent race conditions
    usage = (
        db.query(Usage)
        .filter(Usage.user_id == user_id, Usage.resource_type == resource_type)
        .with_for_update()
        .first()
    )
    if usage is None:
        usage = Usage(user_id=user_id, resource_type=resource_type, used=0)
        db.add(usage)

    usage.used += quantity
    db.commit()
    db.refresh(usage)
    return usage


# ----------------------------
# Usage CRUD
# ----------------------------

def get_usage(db: Session, id: UUID) -> Optional[Usage]:
    """
    Retrieve a usage record by ID.
    
    Args:
        db: Database session
        id: Usage UUID
    
    Returns:
        Usage object if found, None otherwise
    """
    return db.query(Usage).filter(Usage.id == id).first()


def get_usages(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
) -> List[Usage]:
    """
    Retrieve paginated usage records with optional user filtering.
    
    Args:
        db: Database session
        skip: Offset for pagination (default: 0)
        limit: Maximum records to return (default: 100)
        user_id: Filter by user ID (optional)
    
    Returns:
        List of Usage objects
    """
    query = db.query(Usage)
    if user_id is not None:
        query = query.filter(Usage.user_id == user_id)
    return query.offset(skip).limit(limit).all()


def create_usage(db: Session, obj_in: Any) -> Usage:
    """
    Create a new usage record.
    
    Args:
        db: Database session
        obj_in: Usage data (dict, Pydantic model, or object)
    
    Returns:
        Created Usage object
    """
    db_obj = Usage(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_usage(db: Session, db_obj: Usage, obj_in: Any) -> Usage:
    """
    Update an existing usage record.
    
    Args:
        db: Database session
        db_obj: Usage object to update
        obj_in: Update data (dict, object, or Pydantic model)
    
    Returns:
        Updated Usage object
    """
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_usage(db: Session, id: UUID) -> Optional[Usage]:
    """
    Delete a usage record.
    
    Args:
        db: Database session
        id: Usage ID to delete
    
    Returns:
        Deleted Usage object if found, None otherwise
    """
    db_obj = get_usage(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


def get_detailed_status() -> Dict[str, Any]:
    """Get detailed status information for billing service."""
    return {
        "module": "billing_service",
        "status": "operational",
        "timestamp": _utc_now().isoformat(),
    }


def reset_internal_state() -> None:
    """Reset internal state of billing service (for testing)."""
    logger.info("billing_service reset_internal_state called")
