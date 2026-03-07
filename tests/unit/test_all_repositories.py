"""
Comprehensive tests for ALL repository classes targeting near-100% coverage.
"""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch


# ── Base Repository ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_base_repository_all_operations():
    """Test GenericRepository CRUD - covering lines 35-136."""
    from app.repositories.base_repository import GenericRepository
    from app.models.users.user import User  # Use real SQLAlchemy model for select(func.count())

    db = AsyncMock()
    repo = GenericRepository(db, User)

    mock_obj = MagicMock()
    
    # get
    db.get = AsyncMock(return_value=mock_obj)
    result = await repo.get(uuid4())
    assert result is mock_obj

    # get_all
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_obj, mock_obj]
    db.execute = AsyncMock(return_value=mock_result)
    rows = await repo.get_all(skip=0, limit=10)
    assert len(rows) == 2

    # count (requires real model for func.count().select_from())
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 42
    db.execute.return_value = mock_count_result
    count = await repo.count()
    assert count == 42

    # create with auto_commit=True
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    await repo.create({"name": "test"}, auto_commit=True)
    db.commit.assert_called()

    # create with auto_commit=False (flush path)
    db.flush = AsyncMock()
    await repo.create({"name": "test2"}, auto_commit=False)
    db.flush.assert_called()

    # update with dict - auto_commit=True
    db_obj = MagicMock()
    db_obj.name = "old"
    await repo.update(db_obj, {"name": "new"}, auto_commit=True)

    # update with model_dump (pydantic v2)
    mock_schema = MagicMock(spec=["model_dump"])
    mock_schema.model_dump.return_value = {"name": "from_schema"}
    await repo.update(db_obj, mock_schema, auto_commit=True)

    # update with .dict() (pydantic v1)
    mock_schema_v1 = MagicMock(spec=["dict"])
    mock_schema_v1.dict.return_value = {"name": "from_v1"}
    await repo.update(db_obj, mock_schema_v1, auto_commit=True)

    # update - auto_commit=False (flush path)
    await repo.update(db_obj, {"name": "v"}, auto_commit=False)
    db.flush.assert_called()

    # delete by id - found
    db.get.return_value = mock_obj
    db.delete = AsyncMock()
    result = await repo.delete(uuid4(), auto_commit=True)
    db.delete.assert_called()

    # delete by id - not found
    db.get.return_value = None
    result = await repo.delete(uuid4(), auto_commit=True)
    assert result is None

    # delete by model instance directly (isinstance check with User)
    from app.models.users.user import User as UserModel
    mock_user_instance = MagicMock(spec=UserModel)
    db.get.return_value = mock_obj
    result = await repo.delete(mock_user_instance, auto_commit=True)

    # delete - auto_commit=False
    db.get.return_value = mock_obj
    result = await repo.delete(uuid4(), auto_commit=False)
    db.flush.assert_called()

    # Transaction delegation
    await repo.commit()
    await repo.rollback()
    await repo.flush()
    await repo.refresh(mock_obj)


# ── Auth Repository ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_auth_repository_comprehensive():
    from app.repositories.auth_repository import (
        RefreshTokenRepository, EmailVerificationTokenRepository, PasswordResetTokenRepository
    )
    from sqlalchemy.exc import IntegrityError

    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()

    mock_token = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_token
    db.execute = AsyncMock(return_value=mock_result)

    # ── RefreshTokenRepository ──
    rt_repo = RefreshTokenRepository(db)

    # get_by_jti
    result = await rt_repo.get_by_jti("test-jti")
    assert result is mock_token

    # create_safe - success
    db.get = AsyncMock(return_value=mock_token)
    await rt_repo.create_safe({"jti": "abc"}, auto_commit=True)

    # create_safe - IntegrityError
    with patch.object(rt_repo, "create", side_effect=IntegrityError("", {}, None)):
        result = await rt_repo.create_safe({"jti": "dup"})
        assert result is None

    # revoke - found
    with patch.object(rt_repo, "get_by_jti", new_callable=AsyncMock, return_value=mock_token):
        with patch.object(rt_repo, "update", new_callable=AsyncMock, return_value=mock_token):
            result = await rt_repo.revoke("jti1")
            assert result is mock_token

    # revoke - not found
    with patch.object(rt_repo, "get_by_jti", new_callable=AsyncMock, return_value=None):
        result = await rt_repo.revoke("unknown-jti")
        assert result is None

    # delete_expired
    mock_del = MagicMock()
    mock_del.rowcount = 5
    db.execute.return_value = mock_del
    count = await rt_repo.delete_expired()
    assert count == 5

    # delete_expired edge: rowcount=None → 0
    mock_del.rowcount = None
    count = await rt_repo.delete_expired()
    assert count == 0

    db.execute.return_value = mock_result

    # ── EmailVerificationTokenRepository ──
    ev_repo = EmailVerificationTokenRepository(db)

    result = await ev_repo.get_by_jti("ev-jti")
    assert result is mock_token

    db.get = AsyncMock(return_value=mock_token)
    await ev_repo.create_safe({"jti": "ev-1"})

    with patch.object(ev_repo, "create", side_effect=IntegrityError("", {}, None)):
        result = await ev_repo.create_safe({"jti": "dup"})
        assert result is None

    # mark_used - auto_commit=True
    mock_ev_token = MagicMock()
    mock_ev_token.used = False
    await ev_repo.mark_used(mock_ev_token, auto_commit=True)
    assert mock_ev_token.used is True

    # mark_used - auto_commit=False
    mock_ev_token2 = MagicMock()
    mock_ev_token2.used = False
    await ev_repo.mark_used(mock_ev_token2, auto_commit=False)
    assert mock_ev_token2.used is True
    db.flush.assert_called()

    # delete_expired_or_used
    mock_del2 = MagicMock()
    mock_del2.rowcount = 3
    db.execute.return_value = mock_del2
    count = await ev_repo.delete_expired_or_used()
    assert count == 3

    db.execute.return_value = mock_result

    # ── PasswordResetTokenRepository ──
    pr_repo = PasswordResetTokenRepository(db)

    result = await pr_repo.get_by_jti("pr-jti")
    assert result is mock_token

    db.get = AsyncMock(return_value=mock_token)
    await pr_repo.create_safe({"jti": "pr-1"})

    with patch.object(pr_repo, "create", side_effect=IntegrityError("", {}, None)):
        result = await pr_repo.create_safe({"jti": "dup"})
        assert result is None

    mock_pr_token = MagicMock()
    mock_pr_token.used = False
    await pr_repo.mark_used(mock_pr_token, auto_commit=True)
    assert mock_pr_token.used is True

    mock_pr_token2 = MagicMock()
    mock_pr_token2.used = False
    await pr_repo.mark_used(mock_pr_token2, auto_commit=False)
    db.flush.assert_called()

    mock_del3 = MagicMock()
    mock_del3.rowcount = None
    db.execute.return_value = mock_del3
    count = await pr_repo.delete_expired_or_used()
    assert count == 0


# ── User Repository ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_user_repository_comprehensive():
    from app.repositories.user_repository import UserRepository, UserProfileRepository, AdminActionLogRepository
    from sqlalchemy.exc import IntegrityError

    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()

    mock_user = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_result.scalars.return_value.all.return_value = [mock_user]
    mock_result.scalars.return_value.first.return_value = mock_user
    db.execute = AsyncMock(return_value=mock_result)
    db.get = AsyncMock(return_value=mock_user)

    user_repo = UserRepository(db)

    result = await user_repo.get_by_email("test@example.com")
    assert result is mock_user

    await user_repo.create_safe({"email": "a@b.com"})

    with patch.object(user_repo, "create", side_effect=IntegrityError("", {}, None)):
        result = await user_repo.create_safe({"email": "dup@b.com"})
        assert result is None

    result = await user_repo.get_by_stripe_customer_id("cus_123")
    assert result is mock_user

    result = await user_repo.get_with_profile(uuid4())
    assert result is mock_user

    results = await user_repo.get_all_with_profiles()
    assert len(results) == 1

    # has_admin_user: True
    mock_admin = MagicMock()
    mock_admin.scalar_one_or_none.return_value = uuid4()
    db.execute.return_value = mock_admin
    assert await user_repo.has_admin_user() is True

    # has_admin_user: False
    mock_no_admin = MagicMock()
    mock_no_admin.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_no_admin
    assert await user_repo.has_admin_user() is False

    db.execute.return_value = mock_result

    # ── UserProfileRepository ──
    prof_repo = UserProfileRepository(db)

    result = await prof_repo.get_by_user_id(uuid4())
    assert result is not None

    await prof_repo.create_safe({"user_id": uuid4()})

    with patch.object(prof_repo, "create", side_effect=IntegrityError("", {}, None)):
        result = await prof_repo.create_safe({"user_id": uuid4()})
        assert result is None

    # ── AdminActionLogRepository ──
    aal_repo = AdminActionLogRepository(db)
    assert aal_repo.model.__name__ == "AdminActionLog"


# ── Chat Repository ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_chat_repository_comprehensive():
    from app.repositories.chat_repository import ChatSessionRepository, ChatMessageRepository

    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()

    mock_obj = MagicMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_obj
    mock_result.scalars.return_value.all.return_value = [mock_obj, mock_obj]
    db.execute = AsyncMock(return_value=mock_result)

    cs_repo = ChatSessionRepository(db)
    uid = uuid4()

    result = await cs_repo.get(uuid4())
    assert result is mock_obj

    results = await cs_repo.get_for_user(uid)
    assert len(results) == 2

    results = await cs_repo.get_for_business(uuid4())
    assert len(results) == 2

    results = await cs_repo.get_for_idea(uuid4())
    assert len(results) == 2

    # get_all_with_count uses asyncio.gather
    mock_data = MagicMock()
    mock_data.scalars.return_value.all.return_value = [mock_obj]
    mock_count = MagicMock()
    mock_count.scalars.return_value.all.return_value = [mock_obj, mock_obj]

    calls = [0]
    async def mock_execute(stmt):
        calls[0] += 1
        return mock_data if calls[0] % 2 == 1 else mock_count

    db.execute.side_effect = mock_execute
    sessions, total = await cs_repo.get_all_with_count(uid)
    assert total == 2
    db.execute.side_effect = None
    db.execute.return_value = mock_result

    # ChatMessageRepository
    cm_repo = ChatMessageRepository(db)

    result = await cm_repo.get(uuid4())
    assert result is mock_obj

    results = await cm_repo.get_for_session(uuid4())
    assert len(results) == 2

    results = await cm_repo.get_all_filtered(uid)
    assert len(results) == 2


# ── AI Repository ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ai_repository_comprehensive():
    from app.repositories.ai_repository import (
        AgentRepository, AgentRunRepository, ValidationLogRepository, EmbeddingRepository
    )

    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    mock_obj = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_obj
    mock_result.scalars.return_value.all.return_value = [mock_obj]
    db.execute = AsyncMock(return_value=mock_result)

    uid = uuid4()

    agent_repo = AgentRepository(db)
    result = await agent_repo.get_by_name("agent1")
    assert result is mock_obj

    run_repo = AgentRunRepository(db)

    results = await run_repo.get_for_agent(uid)
    assert len(results) == 1

    results = await run_repo.get_for_stage(uid)
    assert len(results) == 1

    result = await run_repo.get_with_stage_and_business(uid)
    assert result is mock_obj

    result = await run_repo.get_with_stage_and_agent(uid)
    assert result is mock_obj

    results = await run_repo.get_all_for_user(uid)
    assert len(results) == 1

    vl_repo = ValidationLogRepository(db)
    results = await vl_repo.get_for_run(uid)
    assert len(results) == 1

    emb_repo = EmbeddingRepository(db)
    results = await emb_repo.get_for_business(uid)
    assert len(results) == 1


# ── Billing Repository ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_billing_repository_comprehensive():
    from app.repositories.billing_repository import (
        PlanRepository, SubscriptionRepository, PaymentMethodRepository,
        PaymentRepository, UsageRepository, ProcessedEventRepository
    )
    from sqlalchemy.exc import IntegrityError

    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()

    mock_obj = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_obj
    mock_result.scalars.return_value.all.return_value = [mock_obj]
    db.execute = AsyncMock(return_value=mock_result)
    db.get = AsyncMock(return_value=mock_obj)

    uid = uuid4()

    # ── PlanRepository ──
    plan_repo = PlanRepository(db)

    results = await plan_repo.get_ordered()
    assert len(results) == 1

    result = await plan_repo.get_by_name("Pro")
    assert result is mock_obj

    result = await plan_repo.get_by_name_excluding("Pro", uid)
    assert result is mock_obj

    result = await plan_repo.get_by_name_for_update("Pro")
    assert result is mock_obj

    await plan_repo.create_safe({"name": "Basic"})

    with patch.object(plan_repo, "create", side_effect=IntegrityError("", {}, None)):
        result = await plan_repo.create_safe({"name": "Dup"})
        assert result is None

    # ── SubscriptionRepository ──
    sub_repo = SubscriptionRepository(db)

    results = await sub_repo.get_for_user(uid)
    assert len(results) == 1

    result = await sub_repo.get_active_for_user(uid)

    result = await sub_repo.get_by_stripe_id("sub_123")
    assert result is mock_obj

    await sub_repo.create_safe({"user_id": uid})

    with patch.object(sub_repo, "create", side_effect=IntegrityError("", {}, None)):
        result = await sub_repo.create_safe({"stripe_subscription_id": "dup"})
        assert result is None

    # ── PaymentMethodRepository ──
    pm_repo = PaymentMethodRepository(db)

    results = await pm_repo.get_for_user(uid)
    assert len(results) == 1

    result = await pm_repo.get_default_for_user(uid)
    assert result is mock_obj

    # ── PaymentRepository ──
    pay_repo = PaymentRepository(db)

    results = await pay_repo.get_all_filtered()
    assert len(results) == 1

    results = await pay_repo.get_all_filtered(user_id=uid, status="completed")
    assert len(results) == 1

    result = await pay_repo.get_pending_by_payment_intent("pi_123")
    assert result is mock_obj

    # ── UsageRepository ──
    usage_repo = UsageRepository(db)

    results = await usage_repo.get_for_user(uid)
    assert len(results) == 1

    result = await usage_repo.get_by_resource(uid, "api_calls", for_update=False)
    assert result is mock_obj

    result = await usage_repo.get_by_resource(uid, "api_calls", for_update=True)
    assert result is mock_obj

    result = await usage_repo.get_by_user_and_resource(uid, "api_calls")
    assert result is mock_obj

    await usage_repo.create_safe({"user_id": uid, "resource_type": "api_calls"})

    with patch.object(usage_repo, "create", side_effect=IntegrityError("", {}, None)):
        result = await usage_repo.create_safe({"user_id": uid, "resource_type": "api_calls"})
        assert result is None

    # upsert_usage - existing record:
    with patch.object(usage_repo, "get_by_resource", new_callable=AsyncMock, return_value=mock_obj):
        with patch.object(usage_repo, "update", new_callable=AsyncMock, return_value=mock_obj):
            result = await usage_repo.upsert_usage({"user_id": uid, "resource_type": "x"})
            assert result is mock_obj

    # upsert_usage - create path:
    with patch.object(usage_repo, "get_by_resource", new_callable=AsyncMock, return_value=None):
        with patch.object(usage_repo, "create_safe", new_callable=AsyncMock, return_value=mock_obj):
            result = await usage_repo.upsert_usage({"user_id": uid, "resource_type": "y"})
            assert result is mock_obj

    # upsert_usage - race condition (create_safe None, retry finds it):
    with patch.object(usage_repo, "get_by_resource", new_callable=AsyncMock) as mock_gbr:
        with patch.object(usage_repo, "create_safe", new_callable=AsyncMock, return_value=None):
            with patch.object(usage_repo, "update", new_callable=AsyncMock, return_value=mock_obj):
                mock_gbr.side_effect = [None, mock_obj]
                result = await usage_repo.upsert_usage({"user_id": uid, "resource_type": "z"})
                assert result is mock_obj

    # upsert_usage - worst case: RuntimeError
    with patch.object(usage_repo, "get_by_resource", new_callable=AsyncMock, return_value=None):
        with patch.object(usage_repo, "create_safe", new_callable=AsyncMock, return_value=None):
            with pytest.raises(RuntimeError):
                await usage_repo.upsert_usage({"user_id": uid, "resource_type": "err"})

    # ── ProcessedEventRepository ──
    pe_repo = ProcessedEventRepository(db)

    result = await pe_repo.get_by_event_id("evt_123", "stripe")
    assert result is mock_obj

    await pe_repo.create_safe({"event_id": "evt_abc", "source": "stripe"})

    with patch.object(pe_repo, "create", side_effect=IntegrityError("", {}, None)):
        result = await pe_repo.create_safe({"event_id": "dup", "source": "stripe"})
        assert result is None


# ── Core Repository ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_core_repository_comprehensive():
    from app.repositories.core_repository import (
        FileRepository, NotificationRepository, ShareLinkRepository, EmailMessageRepository
    )
    from sqlalchemy.exc import IntegrityError

    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()

    mock_obj = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_obj
    mock_result.scalars.return_value.all.return_value = [mock_obj]
    db.execute = AsyncMock(return_value=mock_result)
    db.get = AsyncMock(return_value=mock_obj)

    uid = uuid4()

    file_repo = FileRepository(db)
    results = await file_repo.get_for_owner(uid)
    assert len(results) == 1

    notif_repo = NotificationRepository(db)
    results = await notif_repo.get_for_user(uid)
    assert len(results) == 1
    results = await notif_repo.get_unread_for_user(uid)
    assert len(results) == 1

    sl_repo = ShareLinkRepository(db)
    result = await sl_repo.get_by_token("tok123")
    assert result is mock_obj

    await sl_repo.create_safe({"token": "tok1"})

    with patch.object(sl_repo, "create", side_effect=IntegrityError("", {}, None)):
        result = await sl_repo.create_safe({"token": "dup"})
        assert result is None

    results = await sl_repo.get_for_idea(uid)
    assert len(results) == 1

    results = await sl_repo.get_for_business(uid)
    assert len(results) == 1

    em_repo = EmailMessageRepository(db)
    results = await em_repo.get_pending_or_retrying(limit=20)
    assert len(results) == 1


# ── Partner Repository ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_partner_repository_comprehensive():
    from app.repositories.partner_repository import PartnerProfileRepository, PartnerRequestRepository
    from sqlalchemy.exc import IntegrityError

    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()

    mock_obj = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_obj
    mock_result.scalars.return_value.all.return_value = [mock_obj]
    db.execute = AsyncMock(return_value=mock_result)
    db.get = AsyncMock(return_value=mock_obj)

    uid = uuid4()

    # ── PartnerProfileRepository ──
    pp_repo = PartnerProfileRepository(db)

    result = await pp_repo.get_by_user(uid)
    assert result is mock_obj

    await pp_repo.create_safe({"user_id": uid})

    with patch.object(pp_repo, "create", side_effect=IntegrityError("", {}, None)):
        result = await pp_repo.create_safe({"user_id": uid})
        assert result is None

    results = await pp_repo.get_approved()
    assert len(results) == 1

    # get_approved_by_type - without filter
    results = await pp_repo.get_approved_by_type()
    assert len(results) == 1

    # get_approved_by_type - with filter
    results = await pp_repo.get_approved_by_type(partner_type="tech")
    assert len(results) == 1

    # ── PartnerRequestRepository ──
    pr_repo = PartnerRequestRepository(db)

    results = await pr_repo.get_for_business(uid)
    assert len(results) == 1

    results = await pr_repo.get_for_partner(uid)
    assert len(results) == 1

    result = await pr_repo.get_by_business_and_partner(uid, uuid4())
    assert result is mock_obj

    await pr_repo.create_safe({"business_id": uid, "partner_id": uuid4()})

    with patch.object(pr_repo, "create", side_effect=IntegrityError("", {}, None)):
        result = await pr_repo.create_safe({"business_id": uid})
        assert result is None

    # upsert_request - existing
    with patch.object(pr_repo, "get_by_business_and_partner", new_callable=AsyncMock, return_value=mock_obj):
        with patch.object(pr_repo, "update", new_callable=AsyncMock, return_value=mock_obj):
            result = await pr_repo.upsert_request({"business_id": uid, "partner_id": uuid4()})
            assert result is mock_obj

    # upsert_request - create new
    with patch.object(pr_repo, "get_by_business_and_partner", new_callable=AsyncMock, return_value=None):
        with patch.object(pr_repo, "create", new_callable=AsyncMock, return_value=mock_obj):
            result = await pr_repo.upsert_request({"business_id": uid, "partner_id": uuid4()})
            assert result is mock_obj


# ── Idea Repository ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_idea_repository_comprehensive():
    from app.repositories.idea_repository import (
        IdeaRepository, IdeaVersionRepository, IdeaMetricRepository,
        IdeaComparisonRepository, ComparisonItemRepository, ComparisonMetricRepository,
        ExperimentRepository, IdeaAccessRepository
    )
    from sqlalchemy.exc import IntegrityError

    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()

    mock_obj = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_obj
    mock_result.scalars.return_value.all.return_value = [mock_obj]
    db.execute = AsyncMock(return_value=mock_result)
    db.get = AsyncMock(return_value=mock_obj)

    uid = uuid4()

    # ── IdeaRepository ──
    idea_repo = IdeaRepository(db)

    result = await idea_repo.get_with_relations(uid)
    assert result is mock_obj

    results = await idea_repo.get_all_filtered()
    assert len(results) == 1

    results = await idea_repo.get_all_filtered(user_id=uid)
    assert len(results) == 1

    # ── IdeaVersionRepository ──
    iv_repo = IdeaVersionRepository(db)
    results = await iv_repo.get_for_idea(uid)
    assert len(results) == 1

    # ── IdeaMetricRepository ──
    im_repo = IdeaMetricRepository(db)
    results = await im_repo.get_for_idea(uid)
    assert len(results) == 1

    result = await im_repo.get_by_idea_and_name(uid, "ROI")
    assert result is mock_obj

    # upsert - existing
    with patch.object(im_repo, "get_by_idea_and_name", new_callable=AsyncMock, return_value=mock_obj):
        with patch.object(im_repo, "update", new_callable=AsyncMock, return_value=mock_obj):
            result = await im_repo.upsert(uid, "ROI", 99.0)
            assert result is mock_obj

    # upsert - create new
    with patch.object(im_repo, "get_by_idea_and_name", new_callable=AsyncMock, return_value=None):
        with patch.object(im_repo, "create", new_callable=AsyncMock, return_value=mock_obj):
            result = await im_repo.upsert(uid, "NPV", 50.0)
            assert result is mock_obj

    # ── ExperimentRepository ──
    exp_repo = ExperimentRepository(db)
    results = await exp_repo.get_for_idea(uid)
    assert len(results) == 1

    # ── IdeaAccessRepository ──
    ia_repo = IdeaAccessRepository(db)

    result = await ia_repo.get_by_idea_and_user(uid, uuid4())
    assert result is mock_obj

    await ia_repo.create_safe({"idea_id": uid, "user_id": uuid4()})

    with patch.object(ia_repo, "create", side_effect=IntegrityError("", {}, None)):
        result = await ia_repo.create_safe({"idea_id": uid, "user_id": uuid4()})
        assert result is None

    # upsert - existing
    with patch.object(ia_repo, "get_by_idea_and_user", new_callable=AsyncMock, return_value=mock_obj):
        with patch.object(ia_repo, "update", new_callable=AsyncMock, return_value=mock_obj):
            result = await ia_repo.upsert(uid, uuid4(), {"can_read": True})
            assert result is mock_obj

    # upsert - create
    with patch.object(ia_repo, "get_by_idea_and_user", new_callable=AsyncMock, return_value=None):
        with patch.object(ia_repo, "create", new_callable=AsyncMock, return_value=mock_obj):
            result = await ia_repo.upsert(uid, uuid4(), {"can_read": True})
            assert result is mock_obj

    results = await ia_repo.get_for_idea(uid)
    assert len(results) == 1

    results = await ia_repo.get_for_owner(uid)
    assert len(results) == 1

    # ── IdeaComparisonRepository ──
    ic_repo = IdeaComparisonRepository(db)
    results = await ic_repo.get_for_user(uid)
    assert len(results) == 1

    # ── ComparisonItemRepository ──
    ci_repo = ComparisonItemRepository(db)

    result = await ci_repo.get_by_comparison_and_item(uid, uuid4())
    assert result is mock_obj

    result = await ci_repo.get_by_comparison_and_idea(uid, uuid4())
    assert result is mock_obj

    await ci_repo.create_safe({"comparison_id": uid, "idea_id": uuid4()})

    with patch.object(ci_repo, "create", side_effect=IntegrityError("", {}, None)):
        result = await ci_repo.create_safe({"comparison_id": uid})
        assert result is None

    results = await ci_repo.get_for_comparison(uid)
    assert len(results) == 1

    result = await ci_repo.get_last_rank(uid)
    assert result is mock_obj

    # ── ComparisonMetricRepository ──
    cm_repo = ComparisonMetricRepository(db)

    result = await cm_repo.get_by_comparison_and_metric(uid, "roi")
    assert result is mock_obj

    await cm_repo.create_safe({"comparison_id": uid, "metric_name": "roi"})

    with patch.object(cm_repo, "create", side_effect=IntegrityError("", {}, None)):
        result = await cm_repo.create_safe({"comparison_id": uid})
        assert result is None

    results = await cm_repo.get_for_comparison(uid)
    assert len(results) == 1

    # upsert - existing
    with patch.object(cm_repo, "get_by_comparison_and_metric", new_callable=AsyncMock, return_value=mock_obj):
        with patch.object(cm_repo, "update", new_callable=AsyncMock, return_value=mock_obj):
            result = await cm_repo.upsert(uid, "roi", 1.0)
            assert result is mock_obj

    # upsert - create
    with patch.object(cm_repo, "get_by_comparison_and_metric", new_callable=AsyncMock, return_value=None):
        with patch.object(cm_repo, "create", new_callable=AsyncMock, return_value=mock_obj):
            result = await cm_repo.upsert(uid, "npv", 2.0)
            assert result is mock_obj


# ── Business Repository ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_business_repository_comprehensive():
    from app.repositories.business_repository import (
        BusinessRepository, BusinessCollaboratorRepository,
        BusinessInviteRepository, BusinessInviteIdeaRepository,
        BusinessRoadmapRepository, RoadmapStageRepository
    )
    from app.models.enums import CollaboratorRole
    from sqlalchemy.exc import IntegrityError

    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()

    mock_obj = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_obj
    mock_result.scalars.return_value.all.return_value = [mock_obj]
    db.execute = AsyncMock(return_value=mock_result)
    db.get = AsyncMock(return_value=mock_obj)

    uid = uuid4()

    # ── BusinessRepository ──
    biz_repo = BusinessRepository(db)

    result = await biz_repo.get_with_relations(uid)
    assert result is mock_obj

    with patch.object(biz_repo, "create", new_callable=AsyncMock, return_value=mock_obj):
        await biz_repo.create_safe({"name": "Biz"})

    with patch.object(biz_repo, "create", side_effect=IntegrityError("", {}, None)):
        result = await biz_repo.create_safe({"name": "dup"})
        assert result is None

    results = await biz_repo.get_all_filtered()
    assert len(results) == 1

    results = await biz_repo.get_all_filtered(owner_id=uid)
    assert len(results) == 1

    # ── BusinessCollaboratorRepository ──
    bc_repo = BusinessCollaboratorRepository(db)

    result = await bc_repo.get(uid)
    assert result is mock_obj

    with patch.object(bc_repo, "create", new_callable=AsyncMock, return_value=mock_obj):
        await bc_repo.create_safe({"business_id": uid, "user_id": uuid4()})

    with patch.object(bc_repo, "create", side_effect=IntegrityError("", {}, None)):
        result = await bc_repo.create_safe({"business_id": uid})
        assert result is None

    results = await bc_repo.get_for_business(uid)
    assert len(results) == 1

    result = await bc_repo.get_by_business_and_user(uid, uuid4())
    assert result is mock_obj

    # upsert - existing
    with patch.object(bc_repo, "get_by_business_and_user", new_callable=AsyncMock, return_value=mock_obj):
        with patch.object(bc_repo, "update", new_callable=AsyncMock, return_value=mock_obj):
            result = await bc_repo.upsert(uid, uuid4(), CollaboratorRole.EDITOR)
            assert result is mock_obj

    # upsert - create
    with patch.object(bc_repo, "get_by_business_and_user", new_callable=AsyncMock, return_value=None):
        with patch.object(bc_repo, "create", new_callable=AsyncMock, return_value=mock_obj):
            result = await bc_repo.upsert(uid, uuid4(), CollaboratorRole.VIEWER)
            assert result is mock_obj

    # delete_by_business_and_user - found
    with patch.object(bc_repo, "get_by_business_and_user", new_callable=AsyncMock, return_value=mock_obj):
        result = await bc_repo.delete_by_business_and_user(uid, uuid4())
        assert result is mock_obj

    # delete_by_business_and_user - not found
    with patch.object(bc_repo, "get_by_business_and_user", new_callable=AsyncMock, return_value=None):
        result = await bc_repo.delete_by_business_and_user(uid, uuid4())
        assert result is None

    # ── BusinessInviteRepository ──
    bi_repo = BusinessInviteRepository(db)

    result = await bi_repo.get_by_token("tok")
    assert result is mock_obj

    with patch.object(bi_repo, "create", new_callable=AsyncMock, return_value=mock_obj):
        await bi_repo.create_safe({"token": "t1"})

    with patch.object(bi_repo, "create", side_effect=IntegrityError("", {}, None)):
        result = await bi_repo.create_safe({"token": "dup"})
        assert result is None

    results = await bi_repo.get_for_business(uid)
    assert len(results) == 1

    # ── BusinessInviteIdeaRepository ──
    bii_repo = BusinessInviteIdeaRepository(db)

    result = await bii_repo.get_by_invite_and_idea(uid, uuid4())
    assert result is mock_obj

    with patch.object(bii_repo, "create", new_callable=AsyncMock, return_value=mock_obj):
        await bii_repo.create_safe({"invite_id": uid, "idea_id": uuid4()})

    with patch.object(bii_repo, "create", side_effect=IntegrityError("", {}, None)):
        result = await bii_repo.create_safe({"invite_id": uid})
        assert result is None

    # upsert - existing
    with patch.object(bii_repo, "get_by_invite_and_idea", new_callable=AsyncMock, return_value=mock_obj):
        result = await bii_repo.upsert(uid, uuid4())
        assert result is mock_obj

    # upsert - create
    with patch.object(bii_repo, "get_by_invite_and_idea", new_callable=AsyncMock, return_value=None):
        with patch.object(bii_repo, "create", new_callable=AsyncMock, return_value=mock_obj):
            result = await bii_repo.upsert(uid, uuid4())
            assert result is mock_obj

    # ── BusinessRoadmapRepository ──
    br_repo = BusinessRoadmapRepository(db)

    result = await br_repo.get_by_business(uid)
    assert result is mock_obj

    with patch.object(br_repo, "create", new_callable=AsyncMock, return_value=mock_obj):
        await br_repo.create_safe({"business_id": uid})

    with patch.object(br_repo, "create", side_effect=IntegrityError("", {}, None)):
        result = await br_repo.create_safe({"business_id": uid})
        assert result is None

    # ── RoadmapStageRepository ──
    rs_repo = RoadmapStageRepository(db)

    result = await rs_repo.get_with_relations(uid)
    assert result is mock_obj

    results = await rs_repo.get_for_roadmap(uid)
    assert len(results) == 1

    result = await rs_repo.get_by_order_index(uid, 0)
    assert result is mock_obj

    results = await rs_repo.get_all_for_roadmap_unordered(uid)
    assert len(results) == 1
