import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.billing.subscription_service import (
    SubscriptionService,
    get_subscription_service,
    get_subscription,
    get_subscriptions,
    get_active_subscription,
    create_subscription,
    update_subscription,
    delete_subscription,
)
from app.models import Subscription, Plan
from app.models.enums import SubscriptionStatus
from app.core.exceptions import (
    ResourceNotFoundError,
    DatabaseError,
    ValidationError,
    InvalidStateError,
)

@pytest.fixture
def mock_repos():
    with patch("app.repositories.billing_repository.SubscriptionRepository") as s_repo, \
         patch("app.repositories.billing_repository.PlanRepository") as p_repo, \
         patch("app.repositories.billing_repository.UsageRepository") as u_repo:
        yield s_repo, p_repo, u_repo

@pytest.fixture
def sub_service(mock_repos):
    db = AsyncMock()
    return SubscriptionService(db)

def test_coerce_status():
    assert SubscriptionService._coerce_status("active") == SubscriptionStatus.ACTIVE
    assert SubscriptionService._coerce_status(SubscriptionStatus.PENDING) == SubscriptionStatus.PENDING
    with pytest.raises(ValidationError):
        SubscriptionService._coerce_status("invalid")

def test_validate_status_transition():
    SubscriptionService._validate_status_transition(SubscriptionStatus.PENDING, SubscriptionStatus.ACTIVE)
    with pytest.raises(InvalidStateError):
        SubscriptionService._validate_status_transition(SubscriptionStatus.ACTIVE, SubscriptionStatus.PENDING)
    SubscriptionService._validate_status_transition(SubscriptionStatus.ACTIVE, SubscriptionStatus.ACTIVE)
    with pytest.raises(InvalidStateError):
        SubscriptionService._validate_status_transition(SubscriptionStatus.CANCELED, SubscriptionStatus.ACTIVE)

@pytest.mark.asyncio
async def test_deactivate_other_active_subscriptions(sub_service):
    user_id = uuid4()
    sub_id = uuid4()
    sub1 = MagicMock(spec=Subscription)
    sub1.id = uuid4()
    sub1.status = SubscriptionStatus.ACTIVE
    
    sub_service.repo.get_for_user = AsyncMock(return_value=[sub1])
    
    with patch("app.services.billing.subscription_service.subscriptions_active") as mock_metrics:
        await sub_service._deactivate_other_active_subscriptions(user_id=user_id, keep_subscription_id=sub_id)
        assert sub1.status == SubscriptionStatus.CANCELED
        mock_metrics.dec.assert_called_once()
        
    # Line 62: keep_subscription_id matches row.id
    sub1.id = sub_id
    sub1.status = SubscriptionStatus.ACTIVE
    await sub_service._deactivate_other_active_subscriptions(user_id=user_id, keep_subscription_id=sub_id)
    assert sub1.status == SubscriptionStatus.ACTIVE

@pytest.mark.asyncio
async def test_sync_plan_limits(sub_service):
    sub = MagicMock(spec=Subscription)
    sub.plan_id = uuid4()
    sub.user_id = uuid4()
    
    # Success Case
    plan = MagicMock(spec=Plan)
    plan.name = "PRO"
    sub_service.plan_repo.get = AsyncMock(return_value=plan)
    mock_usage = MagicMock()
    sub_service.usage_repo.get_by_user_and_resource = AsyncMock(return_value=mock_usage)
    sub_service.usage_repo.update = AsyncMock()
    await sub_service._sync_plan_limits(sub)
    
    # Creation Case
    sub_service.usage_repo.get_by_user_and_resource = AsyncMock(return_value=None)
    sub_service.usage_repo.create = AsyncMock()
    await sub_service._sync_plan_limits(sub, auto_commit=False)
    
    # Errors
    sub_service.plan_repo.get = AsyncMock(return_value=None)
    with pytest.raises(ResourceNotFoundError):
        await sub_service._sync_plan_limits(sub)
    
    sub_service.plan_repo.get = AsyncMock(side_effect=Exception("DB fail"))
    with pytest.raises(DatabaseError):
        await sub_service._sync_plan_limits(sub)

@pytest.mark.asyncio
async def test_create_subscription(sub_service):
    user_id = uuid4()
    plan_id = uuid4()
    
    # Missing fields
    with pytest.raises(ValidationError):
        await sub_service.create_subscription({"user_id": user_id})
        
    # Success
    mock_plan = MagicMock()
    mock_sub = MagicMock(spec=Subscription)
    mock_sub.status = SubscriptionStatus.ACTIVE
    mock_sub.user_id = user_id
    mock_sub.id = uuid4()
    
    sub_service.repo.create = AsyncMock(return_value=mock_sub)
    sub_service._sync_plan_limits = AsyncMock()
    sub_service._deactivate_other_active_subscriptions = AsyncMock()
    
    with patch("app.services.billing.plan_service.get_plan", return_value=mock_plan):
        with patch("app.services.billing.subscription_service.subscriptions_active") as mock_metrics:
            await sub_service.create_subscription({"user_id": user_id, "plan_id": plan_id, "status": "active"})
            mock_metrics.inc.assert_called_once()

    # Plan not found
    with patch("app.services.billing.plan_service.get_plan", return_value=None):
        with pytest.raises(ResourceNotFoundError):
            await sub_service.create_subscription({"user_id": user_id, "plan_id": plan_id})

    # Generic error
    with patch("app.services.billing.plan_service.get_plan", side_effect=Exception("Explode")):
        with pytest.raises(DatabaseError):
            await sub_service.create_subscription({"user_id": user_id, "plan_id": plan_id})

@pytest.mark.asyncio
async def test_update_subscription(sub_service):
    db_obj = MagicMock(spec=Subscription)
    db_obj.status = SubscriptionStatus.PENDING
    db_obj.user_id = uuid4()
    db_obj.id = uuid4()
    
    sub_service._sync_plan_limits = AsyncMock()
    sub_service._deactivate_other_active_subscriptions = AsyncMock()
    sub_service.db.commit = AsyncMock()
    
    with patch("app.services.billing.subscription_service.subscriptions_active") as mock_metrics:
        await sub_service.update_subscription(db_obj, {"status": "active"})
        mock_metrics.inc.assert_called()
        
        db_obj.status = SubscriptionStatus.ACTIVE
        await sub_service.update_subscription(db_obj, {"status": "canceled"})
        mock_metrics.dec.assert_called()
        
    # Error Handling
    sub_service.db.commit = AsyncMock(side_effect=Exception("Fail"))
    with pytest.raises(Exception):
        await sub_service.update_subscription(db_obj, {"status": "active"})

@pytest.mark.asyncio
async def test_get_methods(sub_service):
    uid = uuid4()
    sub_service.repo.get = AsyncMock()
    await sub_service.get_subscription(uid)
    
    # 180-182
    sub_service.repo.get_for_user = AsyncMock()
    await sub_service.get_subscriptions(user_id=uid)
    
    sub_service.repo.get_all = AsyncMock()
    await sub_service.get_subscriptions()
    
    # 186
    sub_service.repo.get_active_for_user = AsyncMock()
    await sub_service.get_active_subscription(uid)

@pytest.mark.asyncio
async def test_delete_subscription(sub_service):
    mock_id = uuid4()
    # 280-281
    sub_service.repo.get = AsyncMock(return_value=None)
    assert await sub_service.delete_subscription(mock_id) is None
    
    # 285-286
    mock_sub = MagicMock()
    sub_service.repo.get = AsyncMock(return_value=mock_sub)
    sub_service.db.delete = AsyncMock()
    sub_service.db.commit = AsyncMock()
    await sub_service.delete_subscription(mock_id)
    
    # Error HANDLING
    sub_service.db.commit = AsyncMock(side_effect=Exception("Fail"))
    with pytest.raises(Exception):
        await sub_service.delete_subscription(mock_id)

@pytest.mark.asyncio
async def test_legacy_aliases(sub_service):
    db = sub_service.db
    with patch.object(SubscriptionService, "get_subscription", AsyncMock()):
        await get_subscription(db, uuid4())
    with patch.object(SubscriptionService, "get_subscriptions", AsyncMock()):
        await get_subscriptions(db)
    with patch.object(SubscriptionService, "get_active_subscription", AsyncMock()):
        await get_active_subscription(db, uuid4())
    with patch.object(SubscriptionService, "create_subscription", AsyncMock()):
        await create_subscription(db, {})
    with patch.object(SubscriptionService, "update_subscription", AsyncMock()):
        await update_subscription(db, MagicMock(), {})
    with patch.object(SubscriptionService, "delete_subscription", AsyncMock()):
        await delete_subscription(db, uuid4())

@pytest.mark.asyncio
async def test_get_subscription_service():
    db = AsyncMock()
    await get_subscription_service(db)
