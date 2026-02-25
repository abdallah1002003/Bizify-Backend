"""
Subscription CRUD operations and plan synchronization.
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from app.models import Subscription, Usage
from app.models.enums import SubscriptionStatus
from app.db.database import get_db
from app.services.base_service import BaseService
from app.services.billing import plan_service
from app.services.billing.crud_utils import get_by_id, list_records
from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates
from app.core.exceptions import (
    ResourceNotFoundError,
    InvalidStateError,
    DatabaseError,
    ValidationError
)

logger = logging.getLogger(__name__)


class SubscriptionService(BaseService):
    """Service for managing user subscriptions and plan limit synchronization."""

    def _sync_plan_limits(self, subscription: Subscription, auto_commit: bool = True) -> None:
        """Synchronize usage limits from subscription plan to user's usage record."""
        try:
            plan = plan_service.get_plan(self.db, id=subscription.plan_id)
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
                self.db.query(Usage)
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
                self.db.add(usage)
                logger.info(f"Created usage record for user {subscription.user_id} with limit {limit}")
            else:
                usage.limit_value = limit
                logger.info(f"Updated usage limit for user {subscription.user_id} to {limit}")

            if auto_commit:
                self.db.commit()
            else:
                self.db.flush()
        except ResourceNotFoundError:
            if auto_commit:
                self.db.rollback()
            raise
        except Exception as e:
            logger.error(f"Error syncing plan limits for subscription {subscription.id}: {e}")
            if auto_commit:
                self.db.rollback()
            raise DatabaseError(
                operation="sync_plan_limits",
                entity_type="Subscription",
                original_error=str(e),
                details={"subscription_id": str(subscription.id)}
            )

    def get_subscription(self, id: UUID) -> Optional[Subscription]:
        """Retrieve a single subscription by its unique ID."""
        return get_by_id(self.db, Subscription, id)

    def get_subscriptions(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[UUID] = None,
    ) -> List[Subscription]:
        """Retrieve subscriptions with pagination and optional user filtering."""
        return list_records(
            self.db,
            Subscription,
            skip=skip,
            limit=limit,
            filters={"user_id": user_id},
        )

    def get_active_subscription(self, user_id: UUID) -> Optional[Subscription]:
        """Retrieve the currently active subscription for a user."""
        return (
            self.db.query(Subscription)
            .filter(Subscription.user_id == user_id, Subscription.status == SubscriptionStatus.ACTIVE)
            .first()
        )

    def create_subscription(self, obj_in: Any) -> Subscription:
        """Create a new subscription and synchronize plan usage limits."""
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
            plan = plan_service.get_plan(self.db, id=data["plan_id"])
            if plan is None:
                raise ResourceNotFoundError(
                    resource_type="Plan",
                    resource_id=str(data["plan_id"]),
                    details={"operation": "create_subscription"}
                )
            
            data.setdefault("status", SubscriptionStatus.PENDING)
            data.setdefault("start_date", _utc_now())

            db_obj = Subscription(**data)
            self.db.add(db_obj)
            self.db.flush()

            self._sync_plan_limits(db_obj, auto_commit=False)
            self.db.commit()
            self.db.refresh(db_obj)
            logger.info(f"Created subscription {db_obj.id} for user {db_obj.user_id} with plan {db_obj.plan_id}")
            return db_obj
        except (ValidationError, ResourceNotFoundError) as e:
            self.db.rollback()
            code = getattr(e, "code", "UNKNOWN")
            logger.warning(f"Error {code} in create_subscription: {e}")
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Transaction failed during create_subscription: {e}")
            raise DatabaseError(
                operation="create",
                entity_type="Subscription",
                original_error=str(e),
                details={"input_data": str(data) if 'data' in locals() else None}
            )

    def update_subscription(self, db_obj: Subscription, obj_in: Any) -> Subscription:
        """Update a subscription record and re-sync plan usage limits."""
        try:
            _apply_updates(db_obj, _to_update_dict(obj_in))
            self.db.add(db_obj)
            self.db.commit()
            self.db.refresh(db_obj)

            self._sync_plan_limits(db_obj)
            logger.info(f"Updated subscription {db_obj.id}")
            return db_obj
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating subscription {db_obj.id}: {e}")
            raise

    def delete_subscription(self, id: UUID) -> Optional[Subscription]:
        """Delete a subscription by ID."""
        try:
            db_obj = self.get_subscription(id=id)
            if not db_obj:
                logger.warning(f"Subscription {id} not found")
                return None

            self.db.delete(db_obj)
            self.db.commit()
            logger.info(f"Deleted subscription {id}")
            return db_obj
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting subscription {id}: {e}")
            raise


def get_subscription_service(db: Session = Depends(get_db)) -> SubscriptionService:
    """Dependency provider for SubscriptionService."""
    return SubscriptionService(db)


# ----------------------------
# Legacy Aliases
# ----------------------------

def get_subscription(db: Session, id: UUID) -> Optional[Subscription]:
    return SubscriptionService(db).get_subscription(id)


def get_subscriptions(db: Session, skip: int = 0, limit: int = 100, user_id: Optional[UUID] = None) -> List[Subscription]:
    return SubscriptionService(db).get_subscriptions(skip, limit, user_id)


def get_active_subscription(db: Session, user_id: UUID) -> Optional[Subscription]:
    return SubscriptionService(db).get_active_subscription(user_id)


def create_subscription(db: Session, obj_in: Any) -> Subscription:
    return SubscriptionService(db).create_subscription(obj_in)


def update_subscription(db: Session, db_obj: Subscription, obj_in: Any) -> Subscription:
    return SubscriptionService(db).update_subscription(db_obj, obj_in)


def delete_subscription(db: Session, id: UUID) -> Optional[Subscription]:
    return SubscriptionService(db).delete_subscription(id)
