"""
Repository for Billing domain models:
  - Plan
  - Subscription
  - PaymentMethod
  - Payment
  - Usage

# NOTE (Architecture - Afnan):
# Service → Repository → Database
# Billing services should delegate all persistence to this repository.
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.billing.billing import Plan, Subscription, PaymentMethod, Payment, Usage
from app.models.enums import PaymentStatus
from app.models.billing.processed_event import ProcessedEvent
from app.repositories.base_repository import GenericRepository


class PlanRepository(GenericRepository[Plan]):
    """Repository for Plan model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Plan)

    async def get_ordered(self, skip: int = 0, limit: int = 100) -> List[Plan]:
        """Retrieve plans ordered by active status, price, and name."""
        stmt = (
            select(Plan)
            .order_by(Plan.is_active.desc(), Plan.price.asc(), Plan.name.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_name(self, name: str) -> Optional[Plan]:
        """Retrieve a plan by name (case-insensitive)."""
        stmt = select(Plan).where(func.lower(Plan.name) == name.lower())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name_excluding(self, name: str, exclude_id: UUID) -> Optional[Plan]:
        """Retrieve a plan by name excluding a specific plan ID (for update uniqueness check)."""
        stmt = select(Plan).where(
            func.lower(Plan.name) == name.lower(),
            Plan.id != exclude_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name_for_update(self, name: str) -> Optional[Plan]:
        """
        Retrieve a plan by name with a row lock (SELECT FOR UPDATE).
        
        This variant is used when creating a new plan to prevent race conditions
        where multiple concurrent requests attempt to create plans with the same name.
        The lock ensures that only one transaction can proceed with the creation.
        """
        stmt = select(Plan).where(
            func.lower(Plan.name) == name.lower()
        ).with_for_update()
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_safe(self, obj_in: dict, auto_commit: bool = True) -> Optional[Plan]:
        """Create a plan safely, returning None on IntegrityError (duplicate name)."""
        from sqlalchemy.exc import IntegrityError
        try:
            return await self.create(obj_in, auto_commit=auto_commit)
        except IntegrityError:
            await self.db.rollback()
            return None


class SubscriptionRepository(GenericRepository[Subscription]):
    """Repository for Subscription model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Subscription)

    async def get_for_user(self, user_id: UUID) -> List[Subscription]:
        """Retrieve all subscriptions for a user."""
        stmt = select(Subscription).where(Subscription.user_id == user_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_active_for_user(self, user_id: UUID) -> Optional[Subscription]:
        """Retrieve the active subscription for a user."""
        from app.models.enums import SubscriptionStatus
        stmt = select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.status == SubscriptionStatus.ACTIVE,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_stripe_id(self, stripe_subscription_id: str) -> Optional[Subscription]:
        """Retrieve a subscription by its Stripe subscription ID."""
        stmt = select(Subscription).where(
            Subscription.stripe_subscription_id == stripe_subscription_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_safe(self, obj_in: dict, auto_commit: bool = True) -> Optional[Subscription]:
        """Create a subscription safely, returning None on IntegrityError (duplicate stripe_id)."""
        from sqlalchemy.exc import IntegrityError
        try:
            return await self.create(obj_in, auto_commit=auto_commit)
        except IntegrityError:
            await self.db.rollback()
            return None


class PaymentMethodRepository(GenericRepository[PaymentMethod]):
    """Repository for PaymentMethod model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, PaymentMethod)

    async def get_for_user(self, user_id: UUID) -> List[PaymentMethod]:
        """Retrieve all payment methods for a user."""
        stmt = select(PaymentMethod).where(PaymentMethod.user_id == user_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_default_for_user(self, user_id: UUID) -> Optional[PaymentMethod]:
        """Retrieve the default payment method for a user."""
        stmt = select(PaymentMethod).where(
            PaymentMethod.user_id == user_id,
            PaymentMethod.is_default.is_(True),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_first_for_user(self, user_id: UUID) -> Optional[PaymentMethod]:
        """Retrieve the first (oldest) payment method for a user."""
        stmt = (
            select(PaymentMethod)
            .where(PaymentMethod.user_id == user_id)
            .order_by(PaymentMethod.created_at.asc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


class PaymentRepository(GenericRepository[Payment]):
    """Repository for Payment model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Payment)

    async def get_all_filtered(
        self, skip: int = 0, limit: int = 100, user_id: Optional[UUID] = None, status: Optional[str] = None
    ) -> List[Payment]:
        """Retrieve payments with pagination and optional filtering."""
        stmt = select(Payment)
        if user_id is not None:
            stmt = stmt.where(Payment.user_id == user_id)
        if status is not None:
            stmt = stmt.where(Payment.status == status)
        stmt = stmt.order_by(Payment.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_pending_by_payment_intent(self, stripe_payment_intent_id: str) -> Optional[Payment]:
        """Retrieve the pending payment linked to a Stripe payment intent token_ref."""
        stmt = (
            select(Payment)
            .join(PaymentMethod)
            .where(PaymentMethod.token_ref == stripe_payment_intent_id)
            .where(Payment.status == PaymentStatus.PENDING)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


class UsageRepository(GenericRepository[Usage]):
    """Repository for Usage model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Usage)

    async def get_for_user(self, user_id: UUID) -> List[Usage]:
        """Retrieve all usage records for a user."""
        stmt = select(Usage).where(Usage.user_id == user_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_resource(self, user_id: UUID, resource_type: str, for_update: bool = False) -> Optional[Usage]:
        """Retrieve a single usage record by user and resource type."""
        stmt = select(Usage).where(
            Usage.user_id == user_id,
            Usage.resource_type == resource_type,
        )
        if for_update:
            stmt = stmt.with_for_update()
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_safe(self, obj_in: dict, auto_commit: bool = True) -> Optional[Usage]:
        """Create a usage record safely, returning None on IntegrityError (duplicate)."""
        from sqlalchemy.exc import IntegrityError
        try:
            return await self.create(obj_in, auto_commit=auto_commit)
        except IntegrityError:
            await self.db.rollback()
            return None

    async def get_by_user_and_resource(
        self, user_id: UUID, resource_type: str, for_update: bool = False
    ) -> Optional[Usage]:
        """Backward-compatible alias for get_by_resource."""
        return await self.get_by_resource(user_id, resource_type, for_update=for_update)

    async def upsert_usage(self, obj_in: dict) -> Usage:
        """
        Create or update a usage row for a given (user_id, resource_type) pair.
        
        This method uses SELECT FOR UPDATE to acquire a lock on any existing usage record,
        preventing concurrent modifications. If the record doesn't exist, create_safe() 
        is used to handle any race conditions where another transaction inserts the same 
        (user_id, resource_type) pair concurrently.
        """
        existing = await self.get_by_resource(
            obj_in["user_id"], obj_in["resource_type"], for_update=True
        )
        if existing:
            return await self.update(existing, obj_in)
        
        # Use create_safe to handle race conditions where another transaction
        # inserts the same (user_id, resource_type) pair between our check above
        # and the create call. If it happens, create_safe returns None and we
        # recursively try again.
        created = await self.create_safe(obj_in, auto_commit=True)
        if created is not None:
            return created
        
        # If create_safe returned None (duplicate), retry with locking on existing record
        existing = await self.get_by_resource(
            obj_in["user_id"], obj_in["resource_type"], for_update=True
        )
        if existing:
            return await self.update(existing, obj_in)
        
        # This should not happen in practice, but if it does, raise an error
        raise RuntimeError(
            f"Failed to upsert usage for user {obj_in.get('user_id')} "
            f"and resource {obj_in.get('resource_type')}"
        )

class ProcessedEventRepository(GenericRepository[ProcessedEvent]):
    """Repository for ProcessedEvent model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, ProcessedEvent)

    async def get_by_event_id(self, event_id: str, source: str) -> Optional[ProcessedEvent]:
        """Retrieve a processed event by its event ID and source."""
        stmt = select(ProcessedEvent).where(
            ProcessedEvent.event_id == event_id,
            ProcessedEvent.source == source,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_safe(self, obj_in: dict, auto_commit: bool = True) -> Optional[ProcessedEvent]:
        """Create a processed event safely, returning None on IntegrityError (duplicate)."""
        from sqlalchemy.exc import IntegrityError
        try:
            return await self.create(obj_in, auto_commit=auto_commit)
        except IntegrityError:
            await self.db.rollback()
            return None


class StripeWebhookRepository(GenericRepository[ProcessedEvent]):
    """Repository for Stripe Webhook events (using ProcessedEvent model)."""
    def __init__(self, db: AsyncSession):
        super().__init__(db, ProcessedEvent)
