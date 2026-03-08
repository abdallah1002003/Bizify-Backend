import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from app.services.auth.auth_service import get_auth_service
from app.services.billing.usage_service import UsageService, get_usage_service
from app.services.billing.plan_service import PlanService, get_plan_service
from app.services.billing.subscription_service import SubscriptionService, get_subscription_service
from app.services.billing.payment_service import PaymentService, get_payment_service
from app.services.chat.chat_session_operations import ChatSessionService
from app.services.chat.chat_message_operations import ChatMessageService
from app.services.ai.ai_service import AIService
from app.services.ideation.idea_service import IdeaService
from app.services.users.user_service import get_user_service
from app.services.users.admin_log_service import AdminLogService, get_admin_log_service
from app.services.users.user_profile import UserProfileService, get_user_profile_service
from app.services.partners.partner_profile import PartnerProfileService, get_partner_profile_service
from app.services.partners.partner_request import PartnerRequestService, get_partner_request_service
from app.models.enums import ChatSessionType, ChatRole, SubscriptionStatus, PaymentStatus, UserRole, RequestStatus, PartnerType
from app.core.exceptions import (
    AppException, ValidationError, ResourceNotFoundError, 
    InvalidStateError
)
from app.core import exceptions


def mock_result(data=None, scalar=None):
    """Helper to mock a SQLAlchemy-like result object."""
    res = MagicMock()
    if data is not None:
        scalars = MagicMock()
        scalars.all.return_value = data
        scalars.first.return_value = data[0] if data else None
        res.scalars.return_value = scalars
        if scalar is None:
            res.scalar_one_or_none.return_value = data[0] if data else None
            res.scalar.return_value = data[0] if data else None
    if scalar is not None:
        res.scalar_one_or_none.return_value = scalar
        res.scalar.return_value = scalar
    return res
# ------------------------------------------------------------------------------
# BILLING DOMAIN EXHAUSTIVE
# ------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_usage_service_exhaustive_absolute():
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    service = UsageService(db=mock_db)
    service.repo = AsyncMock()
    user_id = uuid.uuid4()
    
    # Static helpers
    with pytest.raises(exceptions.ValidationError):
        service._normalize_resource_type(" ")
    with pytest.raises(exceptions.ValidationError):
        service._validate_quantity(-1)
        
    # check_usage_limit
    service.repo.get_by_resource.return_value = None
    assert await service.check_usage_limit(user_id, "AI") is True
    service.repo.get_by_resource.return_value = MagicMock(used=10, limit_value=None)
    assert await service.check_usage_limit(user_id, "AI") is True
    service.repo.get_by_resource.return_value = MagicMock(used=5, limit_value=10)
    assert await service.check_usage_limit(user_id, "AI") is True
    service.repo.get_by_resource.return_value = MagicMock(used=10, limit_value=10)
    assert await service.check_usage_limit(user_id, "AI") is False

    # record_usage
    service.repo.get_by_resource.return_value = None
    service.repo.create.return_value = MagicMock(used=0, limit_value=10)
    await service.record_usage(user_id, "AI")
    
    service.repo.get_by_resource.return_value = MagicMock(used=10, limit_value=10)
    with pytest.raises(exceptions.InvalidStateError):
        await service.record_usage(user_id, "AI")
        
    # CRUD
    mock_db.execute.return_value = mock_result(data=[MagicMock()])
    await service.get_usage(uuid.uuid4())
    await service.get_usages(user_id=user_id)
    await service.get_usages(user_id=None)
    
    # create_usage (upsert)
    with pytest.raises(exceptions.ValidationError):
        await service.create_usage({"user_id": user_id})
    with pytest.raises(exceptions.ValidationError):
        await service.create_usage({"user_id": user_id, "resource_type": "AI", "limit_value": -1})
    await service.create_usage({"user_id": user_id, "resource_type": "AI", "used": 5})
    
    # update_usage
    await service.update_usage(MagicMock(), {"resource_type": "AI", "used": 10})
    with pytest.raises(exceptions.ValidationError):
        await service.update_usage(MagicMock(), {"limit_value": -1})
        
    await service.delete_usage(uuid.uuid4())
    await get_usage_service(mock_db)

@pytest.mark.asyncio
async def test_subscription_service_exhaustive_absolute():
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    service = SubscriptionService(db=mock_db)
    service.repo = AsyncMock()
    service.usage_repo = AsyncMock()
    user_id = uuid.uuid4()
    sub_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    
    # _deactivate_other_active_subscriptions
    mock_active = [MagicMock(id=sub_id, status=SubscriptionStatus.ACTIVE), MagicMock(id=uuid.uuid4(), status=SubscriptionStatus.ACTIVE)]
    service.repo.get_for_user.return_value = mock_active
    await service._deactivate_other_active_subscriptions(user_id=user_id, keep_subscription_id=sub_id)
    
    # Helpers
    with pytest.raises(exceptions.ValidationError):
        service._coerce_status("INVALID")
    service._validate_status_transition(SubscriptionStatus.ACTIVE, SubscriptionStatus.ACTIVE)
    with pytest.raises(exceptions.InvalidStateError):
        service._validate_status_transition(SubscriptionStatus.CANCELED, SubscriptionStatus.ACTIVE)

    # _sync_plan_limits
    service.plan_repo = AsyncMock()
    service.plan_repo.get = AsyncMock(return_value=None)
    with pytest.raises(exceptions.ResourceNotFoundError):
        await service._sync_plan_limits(MagicMock(plan_id=plan_id))
            
    service.plan_repo.get = AsyncMock(return_value=MagicMock(name="PRO"))
    service.usage_repo.get_by_user_and_resource = AsyncMock(return_value=None)
    service.usage_repo.create = AsyncMock(return_value=MagicMock())
    await service._sync_plan_limits(MagicMock(plan_id=plan_id))
    
    service.usage_repo.get_by_user_and_resource = AsyncMock(return_value=MagicMock())
    await service._sync_plan_limits(MagicMock(plan_id=plan_id), auto_commit=False)
    
    # Exception branch
    service.plan_repo.get = AsyncMock(side_effect=Exception("fail"))
    # The service catch Exception and raises DatabaseError
    with pytest.raises(exceptions.DatabaseError):
        await service._sync_plan_limits(MagicMock(plan_id=plan_id))
    service.plan_repo.get.side_effect = None

    # create_subscription
    with patch("app.services.billing.subscription_service.plan_service.PlanService") as m_plan_svc_class:
        m_inst = m_plan_svc_class.return_value
        m_inst.get_plan = AsyncMock()
        # Valid Active
        m_inst.get_plan.return_value = MagicMock(id=plan_id)
        service.repo.create = AsyncMock()
        service.repo.create.return_value = MagicMock(id=sub_id, user_id=user_id, plan_id=plan_id, status=SubscriptionStatus.ACTIVE)
        await service.create_subscription({"user_id": user_id, "plan_id": plan_id, "status": SubscriptionStatus.ACTIVE})
        
        # Missing fields
        with pytest.raises(exceptions.ValidationError):
            await service.create_subscription({"user_id": user_id})
        # Plan not found
        m_inst.get_plan.return_value = None
        with pytest.raises(exceptions.ResourceNotFoundError):
            await service.create_subscription({"user_id": user_id, "plan_id": plan_id})
        # Exception branch
        m_inst.get_plan.side_effect = AppException("fail")
        with pytest.raises(exceptions.DatabaseError):
            await service.create_subscription({"user_id": user_id, "plan_id": plan_id})
        m_inst.get_plan.side_effect = None

    # update_subscription
    service.repo.update = AsyncMock()
    mock_sub = MagicMock(id=sub_id, status=SubscriptionStatus.PENDING, user_id=user_id)
    await service.update_subscription(mock_sub, {"status": SubscriptionStatus.ACTIVE})
    # transition to canceled
    await service.update_subscription(MagicMock(status=SubscriptionStatus.ACTIVE, user_id=user_id), {"status": SubscriptionStatus.CANCELED})
    # Error branch
    service.db.commit = AsyncMock(side_effect=exceptions.DatabaseError("fail"))
    with pytest.raises(exceptions.DatabaseError):
        await service.update_subscription(mock_sub, {"status": SubscriptionStatus.ACTIVE})
    service.db.commit.side_effect = None
    
    # delete_subscription
    service.repo.get = AsyncMock()
    service.repo.delete = AsyncMock()
    service.repo.get.return_value = None
    service.repo.delete.return_value = None
    assert await service.delete_subscription(sub_id) is None
    service.repo.get.return_value = mock_sub
    service.repo.delete.return_value = mock_sub
    await service.delete_subscription(sub_id)
    # Error branch
    service.repo.get.side_effect = AppException("fail")
    with pytest.raises(exceptions.AppException):
        await service.delete_subscription(sub_id)
    service.repo.get.side_effect = None
        
    # get_subscriptions & get_active_subscription
    mock_subs = [MagicMock(user_id=user_id, created_at=datetime.now()), MagicMock(user_id=uuid.uuid4(), created_at=datetime.now())]
    service.repo.get_all.return_value = mock_subs
    await service.get_subscriptions(user_id=user_id)
    await service.get_subscriptions(user_id=None)
    await service.get_active_subscription(user_id)

    await get_subscription_service(mock_db)

@pytest.mark.asyncio
async def test_payment_service_exhaustive_absolute():
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    service = PaymentService(db=mock_db)
    service.payment_repo = AsyncMock()
    service.sub_repo = AsyncMock()
    service.method_repo = AsyncMock()
    service.usage_repo = AsyncMock()
    user_id = uuid.uuid4()
    sub_id = uuid.uuid4()
    method_id = uuid.uuid4()
    
    # Helpers
    from app.services.billing.payment_service import _coerce_payment_status, _normalize_currency
    with pytest.raises(ValidationError):
        _coerce_payment_status("INVALID")
    with pytest.raises(ValidationError):
        _normalize_currency("INV_LONG") # Not 3 letter
    with pytest.raises(ValidationError):
        _normalize_currency("IN") # Short

    # get_payments (filtered)
    await service.get_payments(user_id=user_id, status=PaymentStatus.COMPLETED)

    # create_payment
    # Success branch
    service.sub_repo.get.return_value = MagicMock(user_id=user_id)
    service.method_repo.get.return_value = MagicMock(user_id=user_id)
    await service.create_payment({"user_id": user_id, "amount": 10, "subscription_id": sub_id, "payment_method_id": method_id})
    
    # Expanded cases
    with pytest.raises(ValidationError):
        await service.create_payment({"amount": None, "currency": "USD", "status": PaymentStatus.PENDING})
    service.sub_repo.get.return_value = MagicMock(user_id=user_id)
    service.method_repo.get.return_value = MagicMock(user_id=user_id)
    await service.create_payment({"amount": 10, "status": "COMPLETED", "subscription_id": sub_id, "payment_method_id": method_id})
    
    # Error: Invalid amount format
    with pytest.raises(ValidationError):
        await service.create_payment({"amount": "abc"})
    # Error: negative amount
    with pytest.raises(ValidationError):
        await service.create_payment({"amount": -1})
    # Error: sub not found
    service.sub_repo.get.return_value = None
    with pytest.raises(ResourceNotFoundError):
        await service.create_payment({"subscription_id": sub_id, "amount": 10})
    # Error: owner mismatch
    service.sub_repo.get.return_value = MagicMock(user_id=uuid.uuid4())
    with pytest.raises(ValidationError):
        await service.create_payment({"user_id": user_id, "subscription_id": sub_id, "amount": 10})
    # Error: method not found
    service.sub_repo.get.return_value = MagicMock(user_id=user_id)
    service.method_repo.get.return_value = None
    with pytest.raises(ResourceNotFoundError):
        await service.create_payment({"payment_method_id": method_id, "amount": 10})
    # Error: method owner mismatch
    service.method_repo.get = AsyncMock(return_value=MagicMock(user_id=uuid.uuid4()))
    with pytest.raises(ValidationError):
        await service.create_payment({"user_id": user_id, "payment_method_id": method_id, "amount": 10})

    # update_payment
    mock_pmt = MagicMock(status=PaymentStatus.PENDING)
    await service.update_payment(mock_pmt, {"amount": 20, "currency": "eur", "status": PaymentStatus.COMPLETED})
    with pytest.raises(ValidationError):
        await service.update_payment(mock_pmt, {"amount": "abc"})
    with pytest.raises(ValidationError):
        await service.update_payment(mock_pmt, {"amount": -1})
    with pytest.raises(InvalidStateError):
        await service.update_payment(MagicMock(status=PaymentStatus.COMPLETED), {"status": PaymentStatus.FAILED})

    # delete_payment
    payment_id = uuid.uuid4()
    service.payment_repo.get = AsyncMock(return_value=None)
    service.payment_repo.delete = AsyncMock(return_value=MagicMock())
    assert await service.delete_payment(payment_id) is not None
    
    # Correct mocking to return a result when awaited
    mock_payment = MagicMock()
    service.payment_repo.get = AsyncMock(return_value=mock_payment)
    service.payment_repo.delete = AsyncMock(return_value=mock_payment)
    res = await service.delete_payment(payment_id)
    assert res is not None

    # process_payment exhaustive
    user_id = uuid.uuid4()
    sub_id = uuid.uuid4()
    method_id = uuid.uuid4()

    m_sub = MagicMock(user_id=user_id, status=SubscriptionStatus.CANCELED)
    service.sub_repo.get = AsyncMock(return_value=m_sub)
    m_method = MagicMock(user_id=user_id)
    service.method_repo.get = AsyncMock(return_value=m_method)
    
    with patch("app.services.billing.subscription_service.SubscriptionService") as m_sub_svc_class:
        sub_svc_mock = m_sub_svc_class.return_value
        sub_svc_mock.activate_subscription = AsyncMock()
        
        with pytest.raises(exceptions.InvalidStateError):
            await service.process_payment(subscription_id=sub_id, amount=Decimal("10"), method_id=method_id)
            
        m_sub.status = SubscriptionStatus.PENDING
        service.method_repo.get = AsyncMock(return_value=None)
        with pytest.raises(ResourceNotFoundError):
            await service.process_payment(subscription_id=sub_id, amount=Decimal("10"), method_id=method_id)
            
        service.method_repo.get = AsyncMock(return_value=MagicMock(user_id=uuid.uuid4()))
        with pytest.raises(ValidationError):
            await service.process_payment(subscription_id=sub_id, amount=Decimal("10"), method_id=method_id)

        # Success path
        m_sub.status = SubscriptionStatus.PENDING
        service.method_repo.get = AsyncMock(return_value=m_method)
        service.payment_repo.create = AsyncMock(return_value=MagicMock())
        await service.process_payment(subscription_id=sub_id, amount=Decimal("10"), method_id=method_id)
        
        # Success with future end_date
        sub_svc_mock.get_subscription.return_value = MagicMock(user_id=user_id, status=SubscriptionStatus.ACTIVE, end_date=datetime.now(timezone.utc) + timedelta(days=1))
        await service.process_payment(subscription_id=sub_id, amount=Decimal("10"), method_id=method_id)
        
        # Exception branch
        service.sub_repo.get.side_effect = Exception("fail")
        with pytest.raises(Exception, match="fail"):
            await service.process_payment(subscription_id=sub_id, amount=Decimal("10"), method_id=method_id)
        service.sub_repo.get.side_effect = None

    # backward compat (NO MOCKING METHOD UNDER TEST)
    # await service.process_subscription_payment(sub_id, Decimal("10"), method_id) # hit via previous process_payment check logic if desired
    # Instead, call it to hit the wrapper line
    with patch.object(service, "payment_repo", new_callable=AsyncMock) as m_repo, \
         patch.object(service, "method_repo", new_callable=AsyncMock) as m_mrepo, \
         patch.object(service, "sub_repo", new_callable=AsyncMock) as m_srepo:
        
        m_repo.get = AsyncMock(return_value=MagicMock())
        m_srepo.get = AsyncMock(return_value=MagicMock())
        m_mrepo.get = AsyncMock(return_value=MagicMock())
        m_repo.create = AsyncMock(return_value=MagicMock())
        
        await service.create_payment({"amount": 100, "currency": "USD", "subscription_id": uuid.uuid4()})
    
    service.payment_repo.get.return_value = MagicMock(subscription_id=sub_id)
    with patch("app.services.billing.payment_service.subscription_service.SubscriptionService") as m_sub_svc_class:
        m_inst = m_sub_svc_class.return_value
        m_inst.get_subscription = AsyncMock()
        m_inst.get_subscription.return_value = MagicMock(user_id=user_id)
        service.usage_repo.get_for_user = AsyncMock()
        service.usage_repo.get_for_user.return_value = [MagicMock()]
        service.payment_repo.update = AsyncMock()
        service.sub_repo.update = AsyncMock()
        service.usage_repo.update = AsyncMock()
        await service.handle_payment_reversal(uuid.uuid4())

    # handle_payment_reversal errors
    service.payment_repo.get.side_effect = AppException("reversal fail")
    with pytest.raises(exceptions.AppException):
        await service.handle_payment_reversal(uuid.uuid4())
    service.payment_repo.get.side_effect = None
        
    get_payment_service(mock_db)

@pytest.mark.asyncio
async def test_plan_service_exhaustive_absolute():
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    service = PlanService(db=mock_db)
    service.repo = AsyncMock()
    
    # Helpers
    with pytest.raises(ValidationError):
        service._normalize_billing_cycle("INVALID")
    
    # normalize_payload
    with pytest.raises(ValidationError):
        service._normalize_payload({"name": " "})
    with pytest.raises(ValidationError):
        service._normalize_payload({"price": "abc"})
    with pytest.raises(ValidationError):
        service._normalize_payload({"price": -1})
    with pytest.raises(ValidationError):
        service._normalize_payload({"features_json": "abc"})
    # Valid
    service._normalize_payload({"name": "PRO", "price": 10, "features_json": {"custom": 1}})

    # create_plan
    service.repo.get_by_name.return_value = MagicMock()
    with pytest.raises(ValidationError):
        await service.create_plan({"name": "PRO", "price": 10})
    service.repo.get_by_name.return_value = None
    await service.create_plan({"name": "PRO", "price": 10})
    
    # update_plan
    service.repo.get_by_name_excluding.return_value = MagicMock()
    with pytest.raises(ValidationError):
        await service.update_plan(MagicMock(), {"name": "PRO"})
    service.repo.get_by_name_excluding.return_value = None
    await service.update_plan(MagicMock(), {"name": "PRO"})
    
    # CRUD
    await service.get_plans()
    await service.count_plans()
    service.repo.get = AsyncMock(return_value=None)
    service.repo.delete = AsyncMock(return_value=MagicMock())
    assert await service.delete_plan(uuid.uuid4()) is not None
    
    mock_plan = MagicMock()
    service.repo.get = AsyncMock(return_value=mock_plan)
    service.repo.delete = AsyncMock(return_value=mock_plan)
    res = await service.delete_plan(uuid.uuid4())
    assert res is not None
    
    await get_plan_service(mock_db)

# ------------------------------------------------------------------------------
# AUTH & USER DOMAINS (RESTORED & EXPANDED)
# ------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_auth_service_exhaustive_absolute_restored():
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    user_svc = AsyncMock()
    from app.services.auth.auth_service import AuthService
    auth_svc = AuthService(db=mock_db, user_service=user_svc)
    # Ensure attributes exist
    auth_svc.refresh_token_repo = AsyncMock()
    auth_svc.email_verification_repo = AsyncMock()
    auth_svc.password_reset_repo = AsyncMock()
    # auth_svc.repo = auth_svc.refresh_token_repo # Alias just in case
    user_id = uuid.uuid4()
    
    # 1. authenticate_user (Success & Fail)
    user_svc.get_user_by_email.return_value = None
    assert await auth_svc.authenticate_user("e@t.com", "p") is None
    user_svc.get_user_by_email.return_value = MagicMock(password_hash="h", is_active=True, is_verified=True)
    with patch("app.core.security.verify_password", return_value=True):
        await auth_svc.authenticate_user("e@t.com", "p")
    with patch("app.core.security.verify_password", return_value=False):
        assert await auth_svc.authenticate_user("e@t.com", "p") is None
        
    # 2. create_tokens
    with patch("app.services.auth.auth_service.security") as m_sec, \
         patch.object(auth_svc, "_persist_refresh_token", new_callable=AsyncMock):
        m_sec.create_access_token.return_value = "a"
        m_sec.create_refresh_token.return_value = "r"
        await auth_svc.create_tokens(user_id)
        
    # 3. refresh_access_token
    with patch("app.services.auth.auth_service.jwt.decode") as m_decode, \
         patch.object(auth_svc, "_persist_refresh_token", new_callable=AsyncMock) as m_persist, \
         patch("app.services.auth.auth_service.security") as m_sec2:
        m_decode.return_value = {"type": "refresh", "sub": str(user_id), "jti": "j"}
        user_svc.get_user.return_value = MagicMock(id=user_id, is_active=True)
        auth_svc.refresh_token_repo.get_by_jti = AsyncMock(return_value=MagicMock(revoked=False))
        auth_svc.refresh_token_repo.update = AsyncMock()
        m_sec2.create_access_token.return_value = "a2"
        m_sec2.create_refresh_token.return_value = "r2"
        _ = m_persist  # suppress unused warning
        await auth_svc.refresh_access_token("valid_r")
            
    # 4. Password Reset flow
    user_svc.get_user_by_email.return_value = MagicMock(id=user_id, email="e@t.com")
    with patch("app.services.auth.auth_service.security") as m_sec3, \
         patch("app.services.auth.auth_service.jwt.decode") as m_jdec:
        m_sec3.create_password_reset_token.return_value = "fake_reset_token"
        m_jdec.return_value = {"jti": "j2", "exp": 9999999999}
        await auth_svc.request_password_reset("e@t.com")
    
    mock_token = MagicMock(expires_at=datetime.now(timezone.utc) + timedelta(hours=1), user_id=user_id)
    auth_svc.password_reset_repo.get_by_token = AsyncMock(return_value=mock_token)
    reset_payload = {"sub": "e@t.com", "jti": "j3", "exp": 9999999999}
    with patch("app.services.auth.auth_service.security") as m_sec4, \
         patch("app.services.auth.auth_service.jwt.decode") as m_jd4, \
         patch("app.core.token_blacklist.is_token_blacklisted", return_value=False), \
         patch("app.core.token_blacklist.blacklist_token", new_callable=AsyncMock):
        m_sec4.verify_password_reset_token.return_value = reset_payload
        m_sec4.get_password_hash.return_value = "hashed_p2"
        auth_svc.password_reset_repo.get_by_jti = AsyncMock(return_value=MagicMock(used=False, user_id=user_id))
        auth_svc.password_reset_repo.update = AsyncMock()
        user_svc.get_user_by_email.return_value = MagicMock(id=user_id, is_verified=True)
        m_jd4.return_value = {"jti": "j3", "exp": 9999999999}
        await auth_svc.reset_password("t", "p2")
    
    # Static helper
    await get_auth_service(mock_db, user_service=user_svc)

@pytest.mark.asyncio
async def test_user_service_exhaustive_absolute_restored():
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    from app.services.users.user_service import UserService
    # Avoid ModuleNotFoundError
    service = UserService(db=mock_db)
    service.repo = AsyncMock()
    service.profile_repo = AsyncMock()
    service.admin_log_repo = AsyncMock()
    user_id = uuid.uuid4()
    
    # Profile update performer branch
    mock_prof = MagicMock(user_id=user_id)
    service.profile_repo.update.return_value = mock_prof
    await service.update_user_profile(mock_prof, {"bio": "b"}, performer_id=user_id)
    
    # get_users
    await service.get_users(skip=0, limit=10)
    
    # update_user
    mock_user = MagicMock(id=user_id)
    service.repo.get_with_profile.return_value = mock_user
    await service.update_user(mock_user, {"email": "updated@test.com"})
    
    # delete_user
    service.repo.get_with_profile.return_value = mock_user
    service.repo.delete.return_value = mock_user
    await service.delete_user(user_id)
    # delete_user not found
    service.repo.get_with_profile.return_value = None
    service.repo.delete.return_value = None
    assert await service.delete_user(user_id) is None
    
    # Errors in create_user
    service.repo.create.side_effect = AppException("db error")
    with pytest.raises(exceptions.AppException):
        await service.create_user({"email": "new@test.com", "password": "p"})
    service.repo.create.side_effect = None

    # create_user branches (password hash variants)
    # Patch app.core.security directly to avoid ModuleNotFoundError
    with patch("app.core.security.get_password_hash", return_value="hash"):
        await service.create_user({"email": "t@t.com", "password": "p", "role": UserRole.ADMIN})
        await service.create_user({"email": "t2@t.com", "password_hash": "pre", "is_verified": True})
    
    # Missing UserService methods
    await service.get_user_by_email("t@t.com")
    await service.count_users()
    await service.has_admin_user()
    
    # get_user_profile branches
    await service.get_user_profile(id=uuid.uuid4())
    await service.get_user_profile(user_id=uuid.uuid4())
    await service.get_user_profile() # returns None
    
    await service.get_user_profiles()
    await service.create_user_profile({"user_id": user_id})
    
    # update_user with password
    with patch("app.services.users.user_service.get_password_hash", return_value="h"):
        await service.update_user(mock_user, {"password": "p"})
        await service.update_user(mock_user, {"password_hash": "ph"})
        
    # delegation to admin log
    await service.get_admin_action_log(uuid.uuid4())
    await service.get_admin_action_logs()
    await service.create_admin_action_log({})
    await service.update_admin_action_log(MagicMock(), {})
    await service.delete_admin_action_log(uuid.uuid4())
    
    # edge cases in update profile by user id
    service.profile_repo.get_by_user_id.return_value = None
    await service.update_user_profile_by_user_id(user_id, {"bio": "b"})

    # _record_admin_action error
    with pytest.raises(ValueError):
        await service._record_admin_action(admin_id=uuid.uuid4(), action_type="T", target_id=None)

    # create_user with no existing profile
    service.profile_repo.get_by_user_id.return_value = None
    service.repo.create.return_value = MagicMock(id=user_id, email="n@n.com")
    await service.create_user({"email": "n@n.com", "password": "p"})
    
    # delete_user_profile cases
    service.profile_repo.get.return_value = None
    service.profile_repo.delete.return_value = None
    assert await service.delete_user_profile(uuid.uuid4()) is None
    service.profile_repo.get.return_value = MagicMock()
    service.profile_repo.delete.return_value = MagicMock()
    await service.delete_user_profile(uuid.uuid4())

    await get_user_service(mock_db)

@pytest.mark.asyncio
async def test_user_profile_service_exhaustive_absolute():
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    service = UserProfileService(db=mock_db)
    service.repo = AsyncMock()
    service.admin_log_repo = AsyncMock()
    user_id = uuid.uuid4()
    # CRUD
    await service.get_user_profile(user_id)
    await service.get_user_profiles()
    await service.create_user_profile({"user_id": user_id, "bio": "bio"})
    await service.update_user_profile(MagicMock(user_id=user_id), {"bio": "new"}, performer_id=uuid.uuid4())
    await service.update_user_profile_by_user_id(user_id, {"bio": "new2"}, performer_id=uuid.uuid4())
    
    # UserProfile errors & edges
    with pytest.raises(ValueError):
        await service._record_admin_action(None, "TEST", None)
    assert await service.get_user_profile(None, None) is None
    
    # update by user id (upsert)
    service.repo.get_by_user_id.return_value = None
    await service.update_user_profile_by_user_id(user_id, {"bio": "upserted"}, performer_id=uuid.uuid4())

    # delete profile not found
    service.repo.get.return_value = None
    service.repo.get_by_user_id.return_value = None
    service.repo.delete.return_value = None
    assert await service.delete_user_profile(user_id) is None
    
    service.repo.get.return_value = MagicMock()
    service.repo.delete.return_value = MagicMock()
    await service.delete_user_profile(user_id)
    
    get_user_profile_service(mock_db)

@pytest.mark.asyncio
async def test_admin_log_service_exhaustive_absolute():
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    service = AdminLogService(db=mock_db)
    service.repo = AsyncMock()
    # CRUD
    await service.create_admin_action_log({"admin_id": uuid.uuid4(), "action_type": "test", "target_id": uuid.uuid4()})
    
    # Diagnostics
    print(f"DEBUG: AdminLogService attributes: {dir(service)}")
    if hasattr(service, "get_admin_logs"):
        await service.get_admin_logs()
    
    await service.get_admin_action_log(uuid.uuid4())
    await service.get_admin_action_logs()
    await service.update_admin_action_log(MagicMock(), {})
    # delete
    service.repo.get.return_value = None
    service.repo.delete.return_value = None
    assert await service.delete_admin_action_log(uuid.uuid4()) is None
    service.repo.get.return_value = MagicMock()
    service.repo.delete.return_value = MagicMock()
    await service.delete_admin_action_log(uuid.uuid4())
    
    get_admin_log_service(mock_db)

# ------------------------------------------------------------------------------
# PARTNER & CHAT DOMAINS
# ------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_partner_services_exhaustive_absolute():
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    # Profile
    # mock_db.execute.return_value = mock_result(data=[MagicMock()])
    p_prof = PartnerProfileService(db=mock_db)
    p_prof.repo = AsyncMock()
    p_prof.repo.get = AsyncMock(return_value=MagicMock())
    p_prof.repo.get_all = AsyncMock(return_value=[MagicMock()])
    p_prof.repo.create = AsyncMock(return_value=MagicMock())
    p_prof.repo.update = AsyncMock(return_value=MagicMock())
    p_prof.repo.delete = AsyncMock(return_value=MagicMock())
    p_prof.repo.get_approved_by_type = AsyncMock(return_value=[MagicMock()])
    
    await p_prof.get_partner_profile(uuid.uuid4())
    await p_prof.get_partner_profiles()
    # Test with both bio/details and description/services_json
    await p_prof.create_partner_profile({"user_id": uuid.uuid4(), "partner_type": PartnerType.MENTOR, "bio": "b", "details": {"s": 1}})
    await p_prof.create_partner_profile({"user_id": uuid.uuid4(), "partner_type": PartnerType.MENTOR, "description": "d", "services_json": {"s": 2}})
    await p_prof.create_partner_profile({"user_id": uuid.uuid4(), "bio": "b"})
    await p_prof.create_partner_profile({"user_id": uuid.uuid4(), "bio": "b2"})
    # Coverage for bio mapping & model_dump
    await p_prof.create_partner_profile(obj_in={"bio": "bio only"})
    class MockModel:
        def model_dump(self, **kwargs): return {"user_id": uuid.uuid4(), "bio": "m"}
    await p_prof.create_partner_profile(MockModel())
    await p_prof.create_partner_profile(obj_in={"details": {"k": "v"}})
    
    await p_prof.update_partner_profile(MagicMock(), {"bio": "b"})
    await p_prof.approve_partner_profile(uuid.uuid4(), uuid.uuid4())
    # Null case
    p_prof.repo.get.return_value = None
    assert await p_prof.approve_partner_profile(uuid.uuid4(), uuid.uuid4()) is None
    
    # Match
    p_prof.repo.get_approved_by_type.return_value = [
        MagicMock(services_json={"skills": ["AI"]}, experience_json={"industry": "tech"})
    ]
    await p_prof.match_partners_by_capability({"required_type": "consultant", "skills": ["AI"], "industry": "tech", "budget": 100})
    await p_prof.delete_partner_profile(uuid.uuid4())
    get_partner_profile_service(mock_db)
    
    # Request
    # from app.services.partners.partner_request import get_partner_request_service # Already imported
    p_req = PartnerRequestService(db=mock_db)
    p_req.repo = AsyncMock()
    p_req.repo.get = AsyncMock(return_value=MagicMock())
    p_req.repo.get_all = AsyncMock(return_value=[MagicMock()])
    p_req.repo.create = AsyncMock(return_value=MagicMock())
    p_req.repo.update = AsyncMock(return_value=MagicMock())
    p_req.repo.delete = AsyncMock(return_value=MagicMock())
    mock_db.execute.return_value = mock_result(data=[MagicMock()])
    await p_req.get_partner_request(uuid.uuid4())
    await p_req.get_partner_requests()
    await p_req.submit_partner_request(business_id=uuid.uuid4(), partner_id=uuid.uuid4(), context='{"a":1}')
    await p_req.submit_partner_request(business_id=uuid.uuid4(), partner_id=uuid.uuid4(), context='plain')
    await p_req.create_partner_request({"user_id": uuid.uuid4()})
    # model_dump branch
    await p_req.create_partner_request(MockModel())
    # context dict branch
    await p_req.submit_partner_request(business_id=uuid.uuid4(), partner_id=uuid.uuid4())
    await p_req.create_partner_request(obj_in={"business_id": uuid.uuid4()})
    await p_req.update_partner_request(db_obj=MagicMock(), obj_in={"status": RequestStatus.ACCEPTED})
    await p_req.delete_partner_request(id=uuid.uuid4())
    await p_req.transition_request_status(request_id=uuid.uuid4(), new_status=RequestStatus.ACCEPTED)
    await p_req.accept_partner_request(request_id=uuid.uuid4())
    # Null case
    p_req.repo.get = AsyncMock(return_value=None)
    assert await p_req.accept_partner_request(uuid.uuid4()) is None
    
    await p_req.delete_partner_request(uuid.uuid4())
    get_partner_request_service(mock_db)
    
    # PartnerService (wrapper)
    from app.services.partners.partner_service import get_detailed_status, reset_internal_state
    get_detailed_status()
    reset_internal_state()

@pytest.mark.asyncio
async def test_chat_services_exhaustive_absolute():
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    session_svc = ChatSessionService(db=mock_db)
    message_svc = ChatMessageService(db=mock_db)
    # Mocks
    session_svc.repo = AsyncMock()
    message_svc.repo = AsyncMock()
    session_svc.session_repo = session_svc.repo # Alias if used
    message_svc.message_repo = message_svc.repo # Alias if used
    
    # session
    mock_db.execute.return_value = mock_result(data=[MagicMock()])
    await session_svc.get_chat_session(uuid.uuid4())
    await session_svc.get_chat_sessions()
    # Add repo mock
    session_svc.repo = AsyncMock()
    await session_svc.delete_chat_session(uuid.uuid4())
    await session_svc.get_chat_sessions(user_id=uuid.uuid4())
    await session_svc.get_chat_sessions_by_user(uuid.uuid4())
    await session_svc.create_chat_session(user_id=uuid.uuid4(), session_type=ChatSessionType.GENERAL)
    await session_svc.update_chat_session(MagicMock(), {"title": "t2"})
    session_svc.repo.get = AsyncMock(return_value=None)
    await session_svc.delete_chat_session(uuid.uuid4())
    session_svc.repo.get.return_value = MagicMock()
    await session_svc.delete_chat_session(uuid.uuid4())
    session_svc.get_detailed_status()
    
    # message
    mock_db.execute.return_value = mock_result(data=[MagicMock()])
    await message_svc.get_chat_message(uuid.uuid4())
    await message_svc.get_chat_messages()
    await message_svc.get_chat_messages(user_id=uuid.uuid4())
    await message_svc.add_message(session_id=uuid.uuid4(), role=ChatRole.USER, content="c")
    await message_svc.get_session_history(uuid.uuid4())
    await message_svc.update_chat_message(MagicMock(), {"content": "c2"})
    # Add repo mock
    message_svc.repo = AsyncMock()
    message_svc.repo.get = AsyncMock(return_value=None)
    await message_svc.delete_chat_message(uuid.uuid4())
    message_svc.repo.get.return_value = MagicMock()
    await message_svc.delete_chat_message(uuid.uuid4())
    message_svc.get_detailed_status()
    
    # ChatService Facade
    from app.services.chat.chat_service import ChatService
    cs = ChatService(db=mock_db)
    cs._session_svc = AsyncMock()
    cs._message_svc = AsyncMock()
    await cs.get_chat_session(uuid.uuid4())
    await cs.get_chat_session(uuid.uuid4())
    await cs.get_chat_sessions()
    await cs.create_chat_session(user_id=uuid.uuid4(), session_type=ChatSessionType.GENERAL)
    await cs.update_chat_session(MagicMock(), {})
    await cs.delete_chat_session(uuid.uuid4())
    await cs.get_chat_message(uuid.uuid4())
    await cs.get_chat_messages()
    await cs.add_message(session_id=uuid.uuid4(), role=ChatRole.USER, content="c")
    await cs.get_session_history(uuid.uuid4())
    await cs.update_chat_message(MagicMock(), {})
    await cs.delete_chat_message(uuid.uuid4())

@pytest.mark.asyncio
async def test_ideation_services_exhaustive_absolute():
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    access_svc = AsyncMock()
    version_svc = AsyncMock()
    service = IdeaService(db=mock_db, access_service=access_svc, version_service=version_svc)
    service.repo = AsyncMock()
    service.repo.get = AsyncMock(return_value=MagicMock())
    service.repo.get_with_relations = AsyncMock(return_value=MagicMock())
    service.repo.get_all_filtered = AsyncMock(return_value=[MagicMock()])
    service.repo.create = AsyncMock(return_value=MagicMock())
    service.repo.update = AsyncMock(return_value=MagicMock())
    service.repo.delete = AsyncMock(return_value=MagicMock())
    
    idea_id = uuid.uuid4()
    user_id = uuid.uuid4()
    mock_idea = MagicMock(id=idea_id)
    
    await service.get_idea(idea_id, user_id)
    await service.get_ideas(user_id=user_id)
    await service.create_idea({"title": "t"})
    await service.update_idea(mock_idea, {"title": "new"}, performer_id=user_id)
    await service.update_idea(mock_idea, {"bio": "minor"}) # not major
    
    service.repo.delete.return_value = AsyncMock(return_value=MagicMock())
    await service.delete_idea(idea_id)
    await service.check_idea_access(idea_id, user_id)
    
    from app.services.ideation.idea_service import get_idea_service
    await get_idea_service(mock_db)

@pytest.mark.asyncio
async def test_ai_services_exhaustive_absolute():
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    service = AIService(db=mock_db)
    service.agent_repo = AsyncMock()
    service.validation_repo = AsyncMock()
    service.embedding_repo = AsyncMock()
    service.run_repo = AsyncMock()
    agent_id = uuid.uuid4()
    run_id = uuid.uuid4()
    
    # Agent
    mock_db.execute.return_value = mock_result(data=[MagicMock()])
    await service.get_agent(agent_id)
    await service.get_agents()
    await service.create_agent({"name": "a", "prompt": "p"})
    await service.update_agent(MagicMock(), {"name": "n"})
    service.agent_repo.get.return_value = None
    service.agent_repo.delete.return_value = None # Fix return
    assert await service.delete_agent(agent_id) is None
    service.agent_repo.get.return_value = MagicMock()
    await service.delete_agent(agent_id)
    
    # AgentRun
    mock_db.execute.return_value = mock_result(data=[MagicMock()])
    await service.get_agent_run(run_id)
    await service.get_agent_runs()
    await service.get_agent_runs(user_id=uuid.uuid4())
    with patch.object(service, "_agent_run_svc") as m_ars:
        m_ars.return_value.initiate_agent_run = AsyncMock(return_value=MagicMock())
        await service.initiate_agent_run(agent_id=agent_id, user_id=uuid.uuid4(), stage_id=uuid.uuid4(), input_data={})
        
    await service.update_agent_run(MagicMock(), {"status": "completed"})
    service.run_repo.get_with_stage_and_business.return_value = None
    service.run_repo.delete.return_value = None # Fix return
    assert await service.delete_agent_run(run_id) is None
    service.run_repo.get_with_stage_and_business.return_value = MagicMock()
    await service.delete_agent_run(run_id)
    
    # Embedding & Vectorization (Patch class directly in ai_service)
    with patch("app.services.ai.ai_service.EmbeddingService") as m_emb_svc_class:
        m_inst = m_emb_svc_class.return_value
        m_inst.get_embedding = AsyncMock()
        m_inst.get_embeddings = AsyncMock()
        m_inst.create_embedding = AsyncMock()
        m_inst.delete_embedding = AsyncMock()
        m_inst.trigger_vectorization = AsyncMock()
        
        await service.get_embedding(uuid.uuid4())
        await service.get_embeddings()
        await service.create_embedding({"text": "t"})
        await service.delete_embedding(uuid.uuid4())
        await service.trigger_vectorization(uuid.uuid4(), "idea", "content")
    
    # ValidationLog
    await service.get_validation_log(uuid.uuid4())
    await service.get_validation_logs()
    with patch.object(service, "_agent_run_svc") as m_ars:
        m_ars.return_value.record_validation_log = AsyncMock()
        await service.record_validation_log(agent_run_id=uuid.uuid4(), result="passed", details="details")
        
    await service.update_validation_log(MagicMock(), {"log_content": "l2"})
    service.validation_repo.get.return_value = None
    service.validation_repo.delete.return_value = None # Fix return
    assert await service.delete_validation_log(uuid.uuid4()) is None
    service.validation_repo.get.return_value = MagicMock()
    await service.delete_validation_log(uuid.uuid4())
    
    # Internal helpers / Status
    service._billing()
    service._agent_run_svc()
    service.reset_internal_state()
    service.get_detailed_status()
