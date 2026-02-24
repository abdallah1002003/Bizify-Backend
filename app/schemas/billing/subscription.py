"""
Pydantic schemas for subscription-related API requests and responses.

Defines the structure and validation for:
    - SubscriptionCreate: New subscription creation payload
    - SubscriptionUpdate: Subscription modification payload
    - SubscriptionResponse: Subscription info returned from API
    
All schemas enforce subscription status constraints and validate
relationships between users, plans, and usage limits.
"""

from app.models.enums import SubscriptionStatus
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID


class SubscriptionBase(BaseModel):
    """
    Base schema containing common subscription fields.
    
    Used as a foundation for Create, Update, and Response schemas.
    Ensures consistent field definitions across subscription operations.
    
    Attributes:
        user_id: UUID of subscription owner
        plan_id: UUID of billing plan (FREE, PRO, ENTERPRISE)
        status: Current subscription state (ACTIVE, PAUSED, CANCELED, etc.)
        start_date: When subscription activated (optional)
        end_date: When subscription expires or canceled (optional)
    """
    user_id: UUID
    plan_id: UUID
    status: SubscriptionStatus
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class SubscriptionCreate(BaseModel):
    """
    Schema for subscription creation requests.
    
    Used when:
    - User signs up for a plan via POST /api/v1/subscriptions
    - Admin assigns plan to user
    - Automatic subscription renewal
    
    Validation:
    - user_id: Must exist in users table
    - plan_id: Must exist in plans table
    - status: Defaults to PENDING (requires payment verification)
    
    Example:
        >>> data = {
        ...     "user_id": "550e8400-e29b-41d4-a716-446655440000",
        ...     "plan_id": "660e8400-e29b-41d4-a716-446655440000",
        ...     "status": "PENDING"
        ... }
        >>> # POST /api/v1/subscriptions with this payload
        
    Note:
        - Status defaults to PENDING until payment confirmation
        - Dates are auto-calculated on server (not in request)
        - Plan must be available/active to subscribe
    """
    user_id: UUID
    plan_id: UUID
    status: SubscriptionStatus = SubscriptionStatus.PENDING


class SubscriptionUpdate(BaseModel):
    """
    Schema for subscription modification requests.
    
    Used when:
    - User upgrades/downgrades plan via PATCH /api/v1/subscriptions/{id}
    - Admin pauses or activates subscription
    - Subscription renewal extends end_date
    
    All fields optional - only provided fields updated.
    
    Attributes:
        user_id: Change subscription owner (admin only)
        plan_id: Switch to different billing plan
        status: Update subscription state
        start_date: Set activation date (manual admin use)
        end_date: Set expiration date (manual admin use)
        
    Example:
        >>> # Upgrade to PRO plan
        >>> data = {
        ...     "plan_id": "new-plan-uuid",
        ...     "status": "ACTIVE"
        ... }
        >>> # PATCH /api/v1/subscriptions/sub-id with this payload
        
    Note:
        - Plan changes may require prorated billing adjustment
        - Status changes trigger billing/usage updates
        - Dates auto-adjusted for renewals (don't set manually)
    """
    user_id: Optional[UUID] = None
    plan_id: Optional[UUID] = None
    status: Optional[SubscriptionStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class SubscriptionResponse(SubscriptionBase):
    """
    Schema for subscription information returned from API.
    
    Used in responses from:
    - POST /api/v1/subscriptions (after creating)
    - GET /api/v1/subscriptions/{id} (retrieve single)
    - GET /api/v1/subscriptions (list user's subscriptions)
    
    Contains complete subscription details including timestamps
    and links to related resources (plan, user).
    
    Attributes:
        id: Unique UUID for subscription
        user_id: UUID of subscriber
        plan_id: UUID of associated plan
        status: Current state (ACTIVE, PAUSED, CANCELED, EXPIRED, PENDING)
        start_date: When subscription became active
        end_date: When subscription expires or was canceled
        created_at: When subscription record created
        updated_at: When last modified
        
    Example:
        >>> # Response from GET /api/v1/subscriptions/123
        >>> {
        ...     "id": "750e8400-e29b-41d4-a716-446655440000",
        ...     "user_id": "550e8400-e29b-41d4-a716-446655440000",
        ...     "plan_id": "660e8400-e29b-41d4-a716-446655440000",
        ...     "status": "ACTIVE",
        ...     "start_date": "2024-02-01T00:00:00Z",
        ...     "end_date": "2024-03-01T00:00:00Z",
        ...     "created_at": "2024-02-01T10:30:00Z",
        ...     "updated_at": "2024-02-24T15:45:00Z"
        ... }
        
    Status Lifecycle:
        - PENDING: Payment pending, features limited
        - ACTIVE: Subscription active, full access
        - PAUSED: Temporarily paused (preserves usage limits)
        - EXPIRED: End date passed, needs renewal
        - CANCELED: Explicitly canceled by user/admin
        
    Note:
        - from_attributes=True allows reconstruction from ORM
        - Used_limits available from separate Usage model
        - Plan limits synced automatically on status change
    """
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
