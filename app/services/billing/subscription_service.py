"""
Subscription CRUD operations and plan synchronization.
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Subscription, Usage
from app.models.enums import SubscriptionStatus
from app.services.billing import plan_service
from app.services.billing.crud_utils import get_by_id, list_records
from app.services.billing.billing_service import _utc_now, _to_update_dict, _apply_updates
from app.core.exceptions import (
    ResourceNotFoundError,
    InvalidStateError,
    DatabaseError,
    ValidationError
)

logger = logging.getLogger(__name__)


def _sync_plan_limits(db: Session, subscription: Subscription, auto_commit: bool = True) -> None:
    """Synchronize usage limits from subscription plan to user's usage record.
    
    This function maps plan names (FREE, PRO, ENTERPRISE) to usage limits
    and updates or creates the user's Usage record accordingly.
    
    Args:
        db: Database session for queries and commits
        subscription: The subscription whose plan limits should be synced
        auto_commit: If True, commit changes; if False, only flush to session
        
    Returns:
        None
        
    Raises:
        ResourceNotFoundError: If the subscription's plan is not found
        DatabaseError: If database operation fails
    """
    try:
        plan = plan_service.get_plan(db, id=subscription.plan_id)
        if plan is None:
            logger.warning(f"Plan {subscription.plan_id} not found for subscription {subscription.id}")
            raise ResourceNotFoundError(
                resource_type="Plan",
                resource_id=str(subscription.plan_id),
                details={"subscription_id": str(subscription.id)}
            )

        level = (plan.name or "").upper()
        limit_by_plan = {
            "FREE": 10,
            "PRO": 100,
            "ENTERPRISE": 1000,
        }
        limit = limit_by_plan.get(level, 10)

        usage = (
            db.query(Usage)
            .filter(Usage.user_id == subscription.user_id, Usage.resource_type == "AI_REQUEST")
            .first()
        )
        if usage is None:
            usage = Usage(
                user_id=subscription.user_id,
                resource_type="AI_REQUEST",
                used=0,
                limit_value=limit,
            )
            db.add(usage)
            logger.info(f"Created usage record for user {subscription.user_id} with limit {limit}")
        else:
            usage.limit_value = limit
            logger.info(f"Updated usage limit for user {subscription.user_id} to {limit}")

        if auto_commit:
            db.commit()
        else:
            db.flush()
    except ResourceNotFoundError:
        if auto_commit:
            db.rollback()
        raise
    except Exception as e:
        logger.error(f"Error syncing plan limits for subscription {subscription.id}: {e}")
        if auto_commit:
            db.rollback()
        raise DatabaseError(
            operation="sync_plan_limits",
            entity_type="Subscription",
            original_error=str(e),
            details={"subscription_id": str(subscription.id)}
        )


# ----------------------------
# Subscription
# ----------------------------

def get_subscription(db: Session, id: UUID) -> Optional[Subscription]:
    """Retrieve a single subscription by its unique ID.
    
    Args:
        db: Database session
        id: The subscription UUID to retrieve
        
    Returns:
        The Subscription object if found, None otherwise
        
    Raises:
        None
    """
    return get_by_id(db, Subscription, id)


def get_subscriptions(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
) -> List[Subscription]:
    """Retrieve subscriptions with pagination and optional user filtering.
    
    Args:
        db: Database session
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        user_id: Optional filter by user ID
        
    Returns:
        List of Subscription objects
        
    Raises:
        None
    """
    return list_records(
        db,
        Subscription,
        skip=skip,
        limit=limit,
        filters={"user_id": user_id},
    )


def get_active_subscription(db: Session, user_id: UUID) -> Optional[Subscription]:
    """Retrieve the currently active subscription for a user.
    
    Args:
        db: Database session
        user_id: The user's UUID
        
    Returns:
        The active Subscription if one exists, None otherwise
        
    Raises:
        None
    """
    return (
        db.query(Subscription)
        .filter(Subscription.user_id == user_id, Subscription.status == SubscriptionStatus.ACTIVE)
        .first()
    )


def create_subscription(db: Session, obj_in: Any) -> Subscription:
    """Create a new subscription and synchronize plan usage limits.
    
    This function creates a subscription record, sets default status to PENDING,
    and then synchronizes the usage limits from the associated plan.
    
    Args:
        db: Database session
        obj_in: Subscription creation data (dict or Pydantic model)
        
    Returns:
        The created Subscription object
        
    Raises:
        ValidationError: If required fields (user_id, plan_id) are missing
        ResourceNotFoundError: If the plan doesn't exist
        DatabaseError: If database operation fails
    """
    try:
        data = _to_update_dict(obj_in)
        
        # Validate required fields before database operation
        required_fields = {"user_id", "plan_id"}
        missing_fields = required_fields - set(data.keys())
        if missing_fields:
            missing_str = ", ".join(sorted(missing_fields))
            raise ValidationError(
                message=f"Missing required fields: {missing_str}",
                details={"missing_fields": list(missing_fields)}
            )
        
        # Verify plan exists before creating subscription
        plan = plan_service.get_plan(db, id=data["plan_id"])
        if plan is None:
            raise ResourceNotFoundError(
                resource_type="Plan",
                resource_id=str(data["plan_id"]),
                details={"operation": "create_subscription"}
            )
        
        data.setdefault("status", SubscriptionStatus.PENDING)
        data.setdefault("start_date", _utc_now())

        db_obj = Subscription(**data)
        db.add(db_obj)
        db.flush()

        _sync_plan_limits(db, db_obj, auto_commit=False)
        db.commit()
        db.refresh(db_obj)
        logger.info(f"Created subscription {db_obj.id} for user {db_obj.user_id} with plan {db_obj.plan_id}")
        return db_obj
    except (ValidationError, ResourceNotFoundError):
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Transaction failed during create_subscription: {e}")
        raise DatabaseError(
            operation="create",
            entity_type="Subscription",
            original_error=str(e),
            details={"input_data": str(data) if 'data' in locals() else None}
        )


def update_subscription(db: Session, db_obj: Subscription, obj_in: Any) -> Subscription:
    """Update a subscription record and re-sync plan usage limits.
    
    Args:
        db: Database session
        db_obj: The existing Subscription record to update
        obj_in: Updated subscription data (dict or Pydantic model)
        
    Returns:
        The updated Subscription object
        
    Raises:
        Exception: If database operation fails
    """
    try:
        _apply_updates(db_obj, _to_update_dict(obj_in))
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        _sync_plan_limits(db, db_obj)
        logger.info(f"Updated subscription {db_obj.id}")
        return db_obj
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating subscription {db_obj.id}: {e}")
        raise


def delete_subscription(db: Session, id: UUID) -> Optional[Subscription]:
    """Delete a subscription by ID.
    
    Args:
        db: Database session
        id: The subscription UUID to delete
        
    Returns:
        The deleted Subscription object if found, None otherwise
        
    Raises:
        Exception: If database operation fails
    """
    try:
        db_obj = get_subscription(db, id=id)
        if not db_obj:
            logger.warning(f"Subscription {id} not found")
            return None

        db.delete(db_obj)
        db.commit()
        logger.info(f"Deleted subscription {id}")
        return db_obj
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting subscription {id}: {e}")
        raise
