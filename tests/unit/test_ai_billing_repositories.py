"""Exhaustive tests for AI and Billing repository layers resolving coverage gaps."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from sqlalchemy.exc import IntegrityError

class MockRes:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
    
    @property
    def name(self):
        return getattr(self, "_name", "x")
    
    @name.setter
    def name(self, value):
        self._name = value

# ── AI Repositories ───────────────────────────────────────────────────────────

from app.repositories.ai_repository import AgentRepository, AgentRunRepository, ValidationLogRepository, EmbeddingRepository

@pytest.mark.asyncio
async def test_ai_repositories_exhaustive():
    db = AsyncMock()
    
    # AgentRepository
    a_repo = AgentRepository(db)
    
    mock_sc = MagicMock()
    mock_sc.scalar_one_or_none.return_value = MockRes(_name="x")
    db.execute.return_value = mock_sc
    
    res = await a_repo.get_by_name("x")
    assert res.name == "x"
    
    # AgentRunRepository
    r_repo = AgentRunRepository(db)
    uid = uuid4()
    
    mock_all = MagicMock()
    mock_all.scalars().all.return_value = [1, 2]
    db.execute.return_value = mock_all
    
    assert len(await r_repo.get_for_agent(uid)) == 2
    assert len(await r_repo.get_for_stage(uid)) == 2
    
    db.execute.return_value = mock_sc
    res_run = await r_repo.get_with_stage_and_business(uid)
    assert res_run.name == "x"
    res_run_agent = await r_repo.get_with_stage_and_agent(uid)
    assert res_run_agent.name == "x"
    
    db.execute.return_value = mock_all
    assert len(await r_repo.get_all_for_user(uid)) == 2
    
    # ValidationLogRepository
    v_repo = ValidationLogRepository(db)
    assert len(await v_repo.get_for_run(uid)) == 2
    
    # EmbeddingRepository
    e_repo = EmbeddingRepository(db)
    assert len(await e_repo.get_for_business(uid)) == 2


# ── Billing Repositories ──────────────────────────────────────────────────────

from app.repositories.billing_repository import (
    PlanRepository, SubscriptionRepository, PaymentMethodRepository,
    PaymentRepository, UsageRepository, ProcessedEventRepository
)

@pytest.mark.asyncio
async def test_billing_repositories_exhaustive():
    db = AsyncMock()
    uid = uuid4()
    
    # PlanRepository
    pl_repo = PlanRepository(db)
    
    mock_all = MagicMock()
    mock_all.scalars().all.return_value = [1, 2]
    db.execute.return_value = mock_all
    
    assert len(await pl_repo.get_ordered()) == 2
    
    mock_sc = MagicMock()
    mock_sc.scalar_one_or_none.return_value = MockRes(_name="x")
    db.execute.return_value = mock_sc
    
    res_plan = await pl_repo.get_by_name("free")
    assert res_plan.name == "x"
    res_plan_exc = await pl_repo.get_by_name_excluding("free", uid)
    assert res_plan_exc.name == "x"
    res_plan_upd = await pl_repo.get_by_name_for_update("free")
    assert res_plan_upd.name == "x"
    
    with patch.object(pl_repo, "create", new_callable=AsyncMock) as m_create:
        m_create.return_value = MagicMock()
        assert await pl_repo.create_safe({"name": "free"}) is not None
        m_create.side_effect = IntegrityError("a", "b", "c")
        assert await pl_repo.create_safe({"name": "pro"}) is None
        
    # SubscriptionRepository
    sub_repo = SubscriptionRepository(db)
    db.execute.return_value = mock_all
    assert len(await sub_repo.get_for_user(uid)) == 2
    
    db.execute.return_value = mock_sc
    res_sub = await sub_repo.get_active_for_user(uid)
    assert res_sub.name == "x"
    res_sub_stripe = await sub_repo.get_by_stripe_id("sub_1")
    assert res_sub_stripe.name == "x"
    
    with patch.object(sub_repo, "create", new_callable=AsyncMock) as m_create:
        m_create.return_value = MagicMock()
        assert await sub_repo.create_safe({"s": "1"}) is not None
        m_create.side_effect = IntegrityError("a", "b", "c")
        assert await sub_repo.create_safe({"s": "2"}) is None
        
    # PaymentMethodRepository
    pm_repo = PaymentMethodRepository(db)
    db.execute.return_value = mock_all
    assert len(await pm_repo.get_for_user(uid)) == 2
    db.execute.return_value = mock_sc
    res_pm = await pm_repo.get_default_for_user(uid)
    assert res_pm.name == "x"
    
    # PaymentRepository
    p_repo = PaymentRepository(db)
    db.execute.return_value = mock_all
    assert len(await p_repo.get_all_filtered(user_id=uid, status="COMPLETED")) == 2
    db.execute.return_value = mock_sc
    res_pay = await p_repo.get_pending_by_payment_intent("pi_1")
    assert res_pay.name == "x"
    
    # UsageRepository
    u_repo = UsageRepository(db)
    db.execute.return_value = mock_all
    assert len(await u_repo.get_for_user(uid)) == 2
    
    db.execute.return_value = mock_sc
    res_u = await u_repo.get_by_resource(uid, "ai_req")
    assert res_u.name == "x"
    res_u_alias = await u_repo.get_by_user_and_resource(uid, "ai_req")
    assert res_u_alias.name == "x"
    
    with patch.object(u_repo, "create", new_callable=AsyncMock) as m_create:
        m_create.return_value = MagicMock()
        assert await u_repo.create_safe({"u": 1}) is not None
        m_create.side_effect = IntegrityError("a", "b", "c")
        assert await u_repo.create_safe({"u": 2}) is None
        
    # upsert_usage
    with patch.object(u_repo, "get_by_resource", new_callable=AsyncMock) as m_get_res, \
         patch.object(u_repo, "update", new_callable=AsyncMock) as m_upd, \
         patch.object(u_repo, "create_safe", new_callable=AsyncMock) as m_c_safe:
         
         # Path 1: exist
         m_get_res.return_value = MagicMock()
         await u_repo.upsert_usage({"user_id": uid, "resource_type": "r"})
         m_upd.assert_called()
         
         # Path 2: not exist -> create safe success
         m_get_res.return_value = None
         m_c_safe.return_value = MagicMock()
         await u_repo.upsert_usage({"user_id": uid, "resource_type": "r"})
         m_c_safe.assert_called()
         
         # Path 3: not exist -> create safe None -> exist
         m_c_safe.return_value = None
         m_get_res.side_effect = [None, MagicMock()]
         await u_repo.upsert_usage({"user_id": uid, "resource_type": "r"})
         
         # Path 4: RuntimeError double fail
         m_c_safe.return_value = None
         m_get_res.side_effect = [None, None]
         with pytest.raises(RuntimeError):
            await u_repo.upsert_usage({"user_id": uid, "resource_type": "r"})
            
    # ProcessedEventRepository
    pe_repo = ProcessedEventRepository(db)
    db.execute.return_value = mock_sc
    res_pe = await pe_repo.get_by_event_id("ev_1", "src")
    assert res_pe.name == "x"
    
    with patch.object(pe_repo, "create", new_callable=AsyncMock) as m_create:
        m_create.return_value = MagicMock()
        assert await pe_repo.create_safe({"e": "1"}) is not None
        m_create.side_effect = IntegrityError("a", "b", "c")
        assert await pe_repo.create_safe({"e": "2"}) is None
