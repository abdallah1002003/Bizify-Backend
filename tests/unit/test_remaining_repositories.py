"""Exhaustive tests for Business, Chat, Core, Idea, Partner, and User repositories to reach 100%."""
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

@pytest.mark.asyncio
async def test_business_and_chat_repositories_exhaustive():
    db = AsyncMock()
    uid = uuid4()
    
    # ── Business Repositories ──
    from app.repositories.business_repository import BusinessRepository, BusinessCollaboratorRepository, BusinessInviteRepository
    
    b_repo = BusinessRepository(db)
    mock_all = MagicMock()
    mock_all.scalars().all.return_value = [1, 2]
    db.execute.return_value = mock_all
    
    assert len(await b_repo.get_all_filtered(owner_id=uid)) == 2
    
    mock_sc = MagicMock()
    mock_sc.scalar_one_or_none.return_value = MockRes(_name="x")
    mock_sc.scalars().first.return_value = MockRes(_name="x")
    db.execute.return_value = mock_sc
    db.get.return_value = MockRes(_name="x")
    
    with patch.object(b_repo, "create", new_callable=AsyncMock) as m_c:
        m_c.return_value = MagicMock()
        assert await b_repo.create_safe({"a": 1}) is not None
        m_c.side_effect = IntegrityError("a", "b", "c")
        assert await b_repo.create_safe({"a": 2}) is None
    
    res_with_rel = await b_repo.get_with_relations(uid)
    assert res_with_rel.name == "x"
        
    c_repo = BusinessCollaboratorRepository(db)
    db.execute.return_value = mock_all
    assert len(await c_repo.get_for_business(uid)) == 2
    
    db.execute.return_value = mock_sc
    res_coll = await c_repo.get_by_business_and_user(uid, uid)
    assert res_coll.name == "x"
    
    # Generic get
    res_g = await c_repo.get(uid)
    assert res_g.name == "x"
    
    with patch.object(c_repo, "create", new_callable=AsyncMock) as m_c:
        m_c.return_value = MagicMock()
        assert await c_repo.create_safe({"a": 1}) is not None
        m_c.side_effect = IntegrityError("a", "b", "c")
        assert await c_repo.create_safe({"a": 2}) is None
        
    # upsert/delete
    with patch.object(c_repo, "get_by_business_and_user", new_callable=AsyncMock) as m_get_coll:
        m_get_coll.return_value = MagicMock()
        await c_repo.upsert(uid, uid, "ADMIN")
        m_get_coll.return_value = None
        with patch.object(c_repo, "create", new_callable=AsyncMock) as m_cr:
            await c_repo.upsert(uid, uid, "ADMIN")
            m_cr.assert_called()
            
    await c_repo.delete_by_business_and_user(uid, uid)

    i_repo = BusinessInviteRepository(db)
    db.execute.return_value = mock_sc
    res_inv = await i_repo.get_by_token("t")
    assert res_inv.name == "x"
    db.execute.return_value = mock_all
    assert len(await i_repo.get_for_business(uid)) == 2
    
    with patch.object(i_repo, "create", new_callable=AsyncMock) as m_c:
        m_c.return_value = MagicMock()
        assert await i_repo.create_safe({"a": 1}) is not None
        m_c.side_effect = IntegrityError("a", "b", "c")
        assert await i_repo.create_safe({"a": 2}) is None

    # Junctions
    from app.repositories.business_repository import BusinessInviteIdeaRepository
    j_repo = BusinessInviteIdeaRepository(db)
    db.execute.return_value = mock_sc
    await j_repo.get_by_invite_and_idea(uid, uid)
    with patch.object(j_repo, "create", new_callable=AsyncMock) as m_c:
        m_c.side_effect = IntegrityError("a", "b", "c")
        assert await j_repo.create_safe({"a": 1}) is None
    
    with patch.object(j_repo, "get_by_invite_and_idea", new_callable=AsyncMock) as m_get_j:
        m_get_j.return_value = None
        await j_repo.upsert(uid, uid)
        m_get_j.return_value = MagicMock()
        await j_repo.upsert(uid, uid)


    # ── Chat Repositories ──
    from app.repositories.chat_repository import ChatSessionRepository, ChatMessageRepository
    
    cs_repo = ChatSessionRepository(db)
    db.execute.return_value = mock_sc
    res_chat = await cs_repo.get(uid)
    assert res_chat.name == "x"
    
    db.execute.return_value = mock_all
    assert len(await cs_repo.get_for_user(uid)) == 2
    assert len(await cs_repo.get_for_business(uid)) == 2
    assert len(await cs_repo.get_for_idea(uid)) == 2
    
    # get_all_with_count
    with patch("asyncio.gather", new_callable=AsyncMock) as m_gather:
        m_data = MagicMock()
        m_data.scalars().all.return_value = [1, 2, 3]
        m_count = MagicMock()
        m_count.scalars().all.return_value = [1, 2, 3]
        m_gather.return_value = (m_data, m_count)
        sessions, total = await cs_repo.get_all_with_count(uid)
        assert len(sessions) == 3
        assert total == 3

    cm_repo = ChatMessageRepository(db)
    db.execute.return_value = mock_all
    assert len(await cm_repo.get_for_session(uid)) == 2
    assert len(await cm_repo.get_all_filtered(uid)) == 2
    
    db.execute.return_value = mock_sc
    res_msg = await cm_repo.get(uid)
    assert res_msg.name == "x"


# ── Core Repositories ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_core_repositories_exhaustive():
    db = AsyncMock()
    uid = uuid4()
    mock_all = MagicMock()
    mock_all.scalars().all.return_value = [1, 2]
    
    mock_sc = MagicMock()
    mock_sc.scalar_one_or_none.return_value = MockRes(_name="x")
    mock_sc.scalars().first.return_value = MockRes(_name="x")
    db.get.return_value = MockRes(_name="x")
    
    from app.repositories.core_repository import EmailMessageRepository, ShareLinkRepository, FileRepository, NotificationRepository
    
    e_repo = EmailMessageRepository(db)
    db.execute.return_value = mock_all
    assert len(await e_repo.get_pending_or_retrying()) == 2
    
    # FileRepository
    fi_repo = FileRepository(db)
    assert len(await fi_repo.get_for_owner(uid)) == 2
    
    # NotificationRepository
    n_repo = NotificationRepository(db)
    assert len(await n_repo.get_for_user(uid)) == 2
    assert len(await n_repo.get_unread_for_user(uid)) == 2
    
    db.execute.return_value = mock_sc
    s_repo = ShareLinkRepository(db)
    res_sl = await s_repo.get_by_token("x")
    assert res_sl.name == "x"
    
    db.execute.return_value = mock_all
    assert len(await s_repo.get_for_idea(uid)) == 2
    assert len(await s_repo.get_for_business(uid)) == 2
    
    with patch.object(s_repo, "create", new_callable=AsyncMock) as m_c:
        m_c.return_value = MagicMock()
        assert await s_repo.create_safe({"a": 1}) is not None
        m_c.side_effect = IntegrityError("a", "b", "c")
        assert await s_repo.create_safe({"a": 2}) is None
        

# ── Idea Repositories ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_idea_repositories_exhaustive():
    db = AsyncMock()
    uid = uuid4()
    mock_all = MagicMock()
    mock_all.scalars().all.return_value = [1, 2]
    mock_sc = MagicMock()
    mock_sc.scalar_one_or_none.return_value = MockRes(_name="x")
    mock_sc.scalars().first.return_value = MockRes(_name="x")
    db.get.return_value = MockRes(_name="x")
    
    from app.repositories.idea_repository import (
        IdeaRepository, IdeaAccessRepository, IdeaVersionRepository, IdeaMetricRepository, ExperimentRepository
    )
    from app.repositories.idea_repository import IdeaComparisonRepository, ComparisonItemRepository, ComparisonMetricRepository
    
    i_repo = IdeaRepository(db)
    db.execute.return_value = mock_all
    assert len(await i_repo.get_all_filtered(user_id=uid)) == 2
    db.execute.return_value = mock_sc
    res_idea = await i_repo.get_with_relations(uid)
    assert res_idea.name == "x"
    
    im_repo = IdeaMetricRepository(db)
    db.execute.return_value = mock_all
    assert len(await im_repo.get_for_idea(uid)) == 2
    db.execute.return_value = mock_sc
    res_metric = await im_repo.get_by_idea_and_name(uid, "n")
    assert res_metric.name == "x"
    
    # upsert metric
    with patch.object(im_repo, "get_by_idea_and_name", new_callable=AsyncMock) as m_get_met:
        m_get_met.return_value = MagicMock()
        await im_repo.upsert(uid, "n", 1.0)
        m_get_met.return_value = None
        with patch.object(im_repo, "create", new_callable=AsyncMock) as m_c_met:
            await im_repo.upsert(uid, "n", 1.0)
            m_c_met.assert_called()

    ex_repo = ExperimentRepository(db)
    db.execute.return_value = mock_all
    assert len(await ex_repo.get_for_idea(uid)) == 2

    ia_repo = IdeaAccessRepository(db)
    db.execute.return_value = mock_all
    assert len(await ia_repo.get_for_idea(uid)) == 2
    assert len(await ia_repo.get_for_owner(uid)) == 2
    db.execute.return_value = mock_sc
    res_acc = await ia_repo.get_by_idea_and_user(uid, uid)
    assert res_acc.name == "x"
    with patch.object(ia_repo, "create", new_callable=AsyncMock) as m_c_acc:
        m_c_acc.side_effect = IntegrityError("a", "b", "c")
        # rollback called
        assert await ia_repo.create_safe({"a": 1}) is None
    
    # upsert access
    with patch.object(ia_repo, "get_by_idea_and_user", new_callable=AsyncMock) as m_get_acc:
        m_get_acc.return_value = MagicMock()
        await ia_repo.upsert(uid, uid, {"p": True})
        m_get_acc.return_value = None
        with patch.object(ia_repo, "create", new_callable=AsyncMock) as m_c_acc_up:
            await ia_repo.upsert(uid, uid, {"p": True})
            m_c_acc_up.assert_called()
        
    iv_repo = IdeaVersionRepository(db)
    db.execute.return_value = mock_all
    assert len(await iv_repo.get_for_idea(uid)) == 2
    
    ic_repo = IdeaComparisonRepository(db)
    db.execute.return_value = mock_all
    assert len(await ic_repo.get_for_user(uid)) == 2
    db.execute.return_value = mock_sc
    res_comp_gen = await ic_repo.get(uid)
    assert res_comp_gen.name == "x"
    
    ci_repo = ComparisonItemRepository(db)
    db.execute.return_value = mock_all
    assert len(await ci_repo.get_for_comparison(uid)) == 2
    db.execute.return_value = mock_sc
    res_item = await ci_repo.get_by_comparison_and_idea(uid, uid)
    assert res_item.name == "x"
    await ci_repo.get_by_comparison_and_item(uid, uid)
    
    # get_last_rank
    mock_rank = MagicMock()
    mock_rank.scalar_one_or_none.return_value = MockRes(rank_index=5)
    db.execute.return_value = mock_rank
    res_rank = await ci_repo.get_last_rank(uid)
    assert res_rank.rank_index == 5
    
    with patch.object(ci_repo, "create", new_callable=AsyncMock) as m_c_ci:
        m_c_ci.side_effect = IntegrityError("a", "b", "c")
        assert await ci_repo.create_safe({"a": 1}) is None
        
    cm_repo = ComparisonMetricRepository(db)
    db.execute.return_value = mock_all
    assert len(await cm_repo.get_for_comparison(uid)) == 2
    db.execute.return_value = mock_sc
    await cm_repo.get_by_comparison_and_metric(uid, "n")
    
    with patch.object(cm_repo, "create", new_callable=AsyncMock) as m_c_cm:
        m_c_cm.side_effect = IntegrityError("a", "b", "c")
        assert await cm_repo.create_safe({"a": 1}) is None
    
    # upsert comparison metric
    with patch.object(cm_repo, "get_by_comparison_and_metric", new_callable=AsyncMock) as m_get_cm:
        m_get_cm.return_value = MagicMock()
        await cm_repo.upsert(uid, "n", 1.0)
        m_get_cm.return_value = None
        with patch.object(cm_repo, "create", new_callable=AsyncMock) as m_c_cm_up:
            await cm_repo.upsert(uid, "n", 1.0)
            m_c_cm_up.assert_called()


# ── Partner & User Repositories ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_partner_user_repositories_exhaustive():
    db = AsyncMock()
    uid = uuid4()
    mock_all = MagicMock()
    mock_all.scalars().all.return_value = [1, 2]
    mock_sc = MagicMock()
    mock_sc.scalar_one_or_none.return_value = MockRes(_name="x")
    mock_sc.scalars().first.return_value = MockRes(_name="x")
    db.get.return_value = MockRes(_name="x")
    
    from app.repositories.partner_repository import PartnerProfileRepository, PartnerRequestRepository
    from app.repositories.user_repository import UserRepository, UserProfileRepository, AdminActionLogRepository
    
    pp_repo = PartnerProfileRepository(db)
    db.execute.return_value = mock_sc
    res_pp = await pp_repo.get_by_user(uid)
    assert res_pp.name == "x"
    db.execute.return_value = mock_all
    assert len(await pp_repo.get_approved()) == 2
    assert len(await pp_repo.get_approved_by_type("t")) == 2
    
    with patch.object(pp_repo, "create", new_callable=AsyncMock) as m_c_pp:
        m_c_pp.side_effect = IntegrityError("a", "b", "c")
        assert await pp_repo.create_safe({"a": 1}) is None
        
    pr_repo = PartnerRequestRepository(db)
    db.execute.return_value = mock_all
    assert len(await pr_repo.get_for_business(uid)) == 2
    assert len(await pr_repo.get_for_partner(uid)) == 2
    db.execute.return_value = mock_sc
    res_pr = await pr_repo.get_by_business_and_partner(uid, uid)
    assert res_pr.name == "x"
    
    with patch.object(pr_repo, "create", new_callable=AsyncMock) as m_c_pr:
        m_c_pr.side_effect = IntegrityError("a", "b", "c")
        assert await pr_repo.create_safe({"a": 1}) is None
        
    # upsert_request
    with patch.object(pr_repo, "get_by_business_and_partner", new_callable=AsyncMock) as m_get_req:
        m_get_req.return_value = MagicMock()
        await pr_repo.upsert_request({"business_id": uid, "partner_id": uid})
        m_get_req.return_value = None
        with patch.object(pr_repo, "create", new_callable=AsyncMock) as m_c_req:
            await pr_repo.upsert_request({"business_id": uid, "partner_id": uid})
            m_c_req.assert_called()

    u_repo = UserRepository(db)
    db.execute.return_value = mock_sc
    res_u = await u_repo.get_by_email("e@b.com")
    assert res_u.name == "x"
    res_u_stripe = await u_repo.get_by_stripe_customer_id("cus_")
    assert res_u_stripe.name == "x"
    res_u_prof = await u_repo.get_with_profile(uid)
    assert res_u_prof.name == "x"
    db.execute.return_value = mock_all
    assert len(await u_repo.get_all_with_profiles()) == 2
    
    # has_admin_user
    mock_adm = MagicMock()
    mock_adm.scalar_one_or_none.return_value = 1
    db.execute.return_value = mock_adm
    assert await u_repo.has_admin_user() is True

    with patch.object(u_repo, "create", new_callable=AsyncMock) as m_c_u:
        m_c_u.side_effect = IntegrityError("a", "b", "c")
        assert await u_repo.create_safe({"a": 1}) is None
        
    up_repo = UserProfileRepository(db)
    db.execute.return_value = mock_sc
    res_prof = await up_repo.get_by_user_id(uid)
    assert res_prof.name == "x"
    with patch.object(up_repo, "create", new_callable=AsyncMock) as m_c_up:
        m_c_up.side_effect = IntegrityError("a", "b", "c")
        assert await up_repo.create_safe({"a": 1}) is None

    # AdminActionLogRepository
    aal_repo = AdminActionLogRepository(db)
    assert aal_repo is not None
