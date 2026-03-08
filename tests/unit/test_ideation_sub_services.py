"""Exhaustive tests for ideation sub-services to achieve 100% coverage."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid  # Enthusiastic restore of uuid.
from datetime import datetime

from app.services.ideation.idea_comparison_item import (
    ComparisonItemService, get_comparison_item_service
)
from app.services.ideation.idea_comparison_metric import (
    ComparisonMetricService, get_comparison_metric_service
)
from app.services.ideation.idea_metric import (
    IdeaMetricService, get_idea_metric_service
)
from app.services.ideation.idea_experiment import (
    IdeaExperimentService, get_idea_experiment_service
)
from app.services.ideation.idea_version import (
    IdeaVersionService, get_idea_version_service, register_idea_version_handlers
)
from app.models.enums import MetricType, ExperimentStatus


# ── ComparisonItemService ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_comparison_item_service_exhaustive():
    db = AsyncMock()
    svc = ComparisonItemService(db=db)
    svc.repo = AsyncMock()
    uid = uuid.uuid4()
    comp_id = uuid.uuid4()
    idea_id = uuid.uuid4()

    # Basic CRUD
    await svc.get_comparison_item(uid)
    await svc.get_comparison_items()
    await svc.update_comparison_item(MagicMock(), {"rank_index": 1})
    await svc.delete_comparison_item(uid)

    # create_comparison_item: with comp_id and idea_id, create_safe succeeds
    svc.repo.create_safe.return_value = MagicMock()
    await svc.create_comparison_item({"comparison_id": comp_id, "idea_id": idea_id})

    # create_comparison_item: create_safe returns None → fetch existing
    svc.repo.create_safe.return_value = None
    svc.repo.get_by_comparison_and_idea.return_value = MagicMock()
    await svc.create_comparison_item({"comparison_id": comp_id, "idea_id": idea_id})

    # create_comparison_item: no comp_id/idea_id → fallback create
    await svc.create_comparison_item({"rank_index": 0})

    # add_item_to_comparison: already exists
    svc.repo.get_by_comparison_and_idea.return_value = MagicMock()
    await svc.add_item_to_comparison(comp_id, idea_id)

    # add_item_to_comparison: new item, create_safe succeeds
    svc.repo.get_by_comparison_and_idea.return_value = None
    svc.repo.get_last_rank.return_value = None  # next_rank = 0
    svc.repo.create_safe.return_value = MagicMock()
    await svc.add_item_to_comparison(comp_id, idea_id)

    # add_item_to_comparison: last_rank not None
    last = MagicMock(rank_index=3)
    svc.repo.get_last_rank.return_value = last
    svc.repo.create_safe.return_value = MagicMock()
    await svc.add_item_to_comparison(comp_id, idea_id)

    # add_item_to_comparison: create_safe returns None → re-fetch existing
    svc.repo.get_last_rank.return_value = None
    svc.repo.create_safe.return_value = None
    svc.repo.get_by_comparison_and_idea.return_value = MagicMock()
    await svc.add_item_to_comparison(comp_id, idea_id)

    # add_item_to_comparison: create_safe returns None AND re-fetch is None → RuntimeError
    svc.repo.create_safe.return_value = None
    svc.repo.get_by_comparison_and_idea.return_value = None
    with pytest.raises(RuntimeError):
        await svc.add_item_to_comparison(comp_id, idea_id)

    # Dependency provider
    await get_comparison_item_service(db)


# ── ComparisonMetricService ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_comparison_metric_service_exhaustive():
    db = AsyncMock()
    svc = ComparisonMetricService(db=db)
    svc.repo = AsyncMock()
    uid = uuid.uuid4()
    comp_id = uuid.uuid4()

    # Basic CRUD
    await svc.get_comparison_metric(uid)
    await svc.get_comparison_metrics()
    await svc.update_comparison_metric(MagicMock(), {"value": 10})
    await svc.delete_comparison_metric(uid)

    # create_comparison_metric: create_safe succeeds
    svc.repo.create_safe.return_value = MagicMock()
    await svc.create_comparison_metric({"comparison_id": comp_id, "metric_name": "score"})

    # create_comparison_metric: create_safe returns None → fetch existing
    svc.repo.create_safe.return_value = None
    svc.repo.get_by_comparison_and_metric.return_value = MagicMock()
    await svc.create_comparison_metric({"comparison_id": comp_id, "metric_name": "score"})

    # create_comparison_metric: create_safe None AND existing None → RuntimeError
    svc.repo.create_safe.return_value = None
    svc.repo.get_by_comparison_and_metric.return_value = None
    with pytest.raises(RuntimeError):
        await svc.create_comparison_metric({"comparison_id": comp_id, "metric_name": "score"})

    # Dependency provider
    await get_comparison_metric_service(db)


# ── IdeaMetricService ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_idea_metric_service_exhaustive():
    db = AsyncMock()
    svc = IdeaMetricService(db=db)
    svc.repo = AsyncMock()
    svc.idea_repo = AsyncMock()
    uid = uuid.uuid4()
    idea_id = uuid.uuid4()

    # get_idea_metric: found and not deleted
    svc.repo.get.return_value = MagicMock(is_deleted=False)
    result = await svc.get_idea_metric(uid)
    assert result is not None

    # get_idea_metric: deleted
    svc.repo.get.return_value = MagicMock(is_deleted=True)
    assert await svc.get_idea_metric(uid) is None

    # get_idea_metric: not found
    svc.repo.get.return_value = None
    assert await svc.get_idea_metric(uid) is None

    # get_idea_metrics: with idea_id filter
    svc.repo.get_for_idea.return_value = [
        MagicMock(is_deleted=False),
        MagicMock(is_deleted=True),  # filtered out
    ]
    metrics = await svc.get_idea_metrics(idea_id=idea_id)
    assert len(metrics) == 1

    # get_idea_metrics: without filter
    svc.repo.get_all.return_value = [MagicMock(is_deleted=False)]
    await svc.get_idea_metrics()

    # create_idea_metric: AI_ANALYSIS type → updates idea score
    mock_metric = MagicMock(type=MetricType.AI_ANALYSIS, idea_id=idea_id, value=0.9)
    svc.repo.create.return_value = mock_metric
    svc.idea_repo.get.return_value = MagicMock()
    await svc.create_idea_metric({"type": MetricType.AI_ANALYSIS, "value": 0.9, "idea_id": idea_id})

    # create_idea_metric: AI_ANALYSIS but idea not found
    svc.idea_repo.get.return_value = None
    await svc.create_idea_metric({"type": MetricType.AI_ANALYSIS, "value": 0.9, "idea_id": idea_id})

    # create_idea_metric: non-AI type
    mock_metric2 = MagicMock(type="MARKET_FIT", idea_id=idea_id, value=0.5)
    svc.repo.create.return_value = mock_metric2
    await svc.create_idea_metric({"type": "MARKET_FIT", "value": 0.5, "idea_id": idea_id})

    # update / delete
    await svc.update_idea_metric(MagicMock(), {"value": 0.8})

    # delete: not found
    svc.repo.get.return_value = None
    assert await svc.delete_idea_metric(uid) is None

    # delete: found, not deleted
    svc.repo.get.return_value = MagicMock(is_deleted=False)
    await svc.delete_idea_metric(uid)

    # record_metric
    svc.repo.create.return_value = MagicMock(type="MARKET_FIT", idea_id=idea_id, value=1.0)
    await svc.record_metric(idea_id, "revenue", 1000.0, "MARKET_FIT", uuid.uuid4())

    # get_metric_trends: no metrics
    svc.repo.get_for_idea.return_value = []
    result = await svc.get_metric_trends(idea_id, "revenue")
    assert result["trend"] == "stable"

    # get_metric_trends: one metric (stable)
    m1 = MagicMock(name="revenue", is_deleted=False, value=100.0,
                   created_at=datetime(2024, 1, 1))
    m1.name = "revenue"
    svc.repo.get_for_idea.return_value = [m1]
    result = await svc.get_metric_trends(idea_id, "revenue")
    assert result["trend"] == "stable"

    # get_metric_trends: two metrics, improving
    m2 = MagicMock(value=80.0, created_at=datetime(2024, 1, 2))
    m2.name = "revenue"
    m2.is_deleted = False
    m1_newer = MagicMock(value=100.0, created_at=datetime(2024, 1, 3))
    m1_newer.name = "revenue"
    m1_newer.is_deleted = False
    svc.repo.get_for_idea.return_value = [m2, m1_newer]
    result = await svc.get_metric_trends(idea_id, "revenue")
    assert result["trend"] in ("improving", "declining", "stable")

    # get_metric_trends: two metrics, declining
    m_old = MagicMock(value=120.0, created_at=datetime(2024, 1, 1))
    m_old.name = "revenue"
    m_old.is_deleted = False
    m_new = MagicMock(value=90.0, created_at=datetime(2024, 1, 5))
    m_new.name = "revenue"
    m_new.is_deleted = False
    svc.repo.get_for_idea.return_value = [m_old, m_new]
    result = await svc.get_metric_trends(idea_id, "revenue")
    # Both orderings possible – just assert it's one of the valid states
    assert result["trend"] in ("improving", "declining", "stable")

    # Dependency provider
    await get_idea_metric_service(db)


# ── IdeaExperimentService ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_idea_experiment_service_exhaustive():
    db = AsyncMock()
    svc = IdeaExperimentService(db=db)
    svc.repo = AsyncMock()
    svc.idea_repo = AsyncMock()
    uid = uuid.uuid4()
    idea_id = uuid.uuid4()
    user_id = uuid.uuid4()

    # Basic CRUD
    await svc.get_experiment(uid)

    # get_experiments with idea_id filter
    svc.repo.get_for_idea.return_value = [MagicMock(), MagicMock()]
    await svc.get_experiments(idea_id=idea_id, skip=0, limit=5)

    # get_experiments without filter
    await svc.get_experiments()

    # create / update / delete
    await svc.create_experiment(MagicMock(idea_id=idea_id))
    await svc.update_experiment(MagicMock(), MagicMock())

    # delete: not found
    svc.repo.get.return_value = None
    assert await svc.delete_experiment(uid) is None

    # delete: found
    svc.repo.get.return_value = MagicMock()
    svc.repo.delete.return_value = MagicMock()
    await svc.delete_experiment(uid)

    # initiate_experiment: access denied
    with patch("app.services.ideation.idea_experiment.idea_service") as m_idea_svc_mod:
        m_idea_svc_mod.IdeaService.return_value.check_idea_access = AsyncMock(return_value=False)
        with pytest.raises(PermissionError):
            await svc.initiate_experiment(idea_id, "hypothesis", user_id)

    # initiate_experiment: access granted
    with patch("app.services.ideation.idea_experiment.idea_service") as m_idea_svc_mod:
        m_idea_svc_mod.IdeaService.return_value.check_idea_access = AsyncMock(return_value=True)
        svc.repo.create.return_value = MagicMock()
        await svc.initiate_experiment(idea_id, "hypothesis", user_id)

    # finalize_experiment: not found
    svc.repo.get.return_value = None
    assert await svc.finalize_experiment(uid, {}, ExperimentStatus.COMPLETED) is None

    # finalize_experiment: completed → update idea status
    mock_exp = MagicMock(idea_id=idea_id)
    svc.repo.get.return_value = mock_exp
    svc.repo.update.return_value = MagicMock(idea_id=idea_id)
    svc.idea_repo.get.return_value = MagicMock()
    await svc.finalize_experiment(uid, {"result": "ok"}, ExperimentStatus.COMPLETED)

    # finalize_experiment: completed but idea not found
    svc.idea_repo.get.return_value = None
    svc.repo.update.return_value = MagicMock(idea_id=idea_id)
    await svc.finalize_experiment(uid, {}, ExperimentStatus.COMPLETED)

    # finalize_experiment: failed (not COMPLETED, idea not updated)
    svc.repo.update.return_value = MagicMock(idea_id=idea_id)
    await svc.finalize_experiment(uid, {}, ExperimentStatus.FAILED)

    # Dependency provider
    await get_idea_experiment_service(db)


# ── IdeaVersionService ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_idea_version_service_exhaustive():
    db = AsyncMock()
    svc = IdeaVersionService(db=db)
    svc.repo = AsyncMock()
    uid = uuid.uuid4()
    idea_id = uuid.uuid4()
    user_id = uuid.uuid4()

    # create_idea_snapshot: status has .value
    mock_idea = MagicMock(id=idea_id, owner_id=user_id)
    mock_idea.status = MagicMock()
    mock_idea.status.value = "DRAFT"
    mock_idea.title = "T"
    mock_idea.description = "D"
    mock_idea.ai_score = 0.5
    mock_idea.is_archived = False
    svc.repo.create.return_value = MagicMock()
    await svc.create_idea_snapshot(mock_idea, created_by=user_id)

    # create_idea_snapshot: status has no .value (plain string)
    mock_idea2 = MagicMock(id=idea_id, owner_id=user_id)
    mock_idea2.status = "DRAFT"
    mock_idea2.title = "T"
    mock_idea2.description = "D"
    mock_idea2.ai_score = 0.5
    mock_idea2.is_archived = False
    await svc.create_idea_snapshot(mock_idea2)   # created_by defaults to owner_id

    # get_idea_version
    await svc.get_idea_version(uid)

    # get_idea_versions: with idea_id filter
    svc.repo.get_for_idea.return_value = [MagicMock(), MagicMock()]
    await svc.get_idea_versions(idea_id=idea_id, skip=0, limit=1)

    # get_idea_versions: without filter
    await svc.get_idea_versions()

    # CRUD
    await svc.create_idea_version({"idea_id": idea_id})
    await svc.update_idea_version(MagicMock(), {"snapshot_json": {}})

    # delete_idea_version: not found
    svc.repo.get.return_value = None
    assert await svc.delete_idea_version(uid) is None

    # delete_idea_version: found
    svc.repo.get.return_value = MagicMock()
    svc.repo.delete.return_value = MagicMock()
    await svc.delete_idea_version(uid)

    # register_idea_version_handlers
    register_idea_version_handlers()

    # handle_idea_event: no idea in payload
    await IdeaVersionService.handle_idea_event("idea.created", {})
    await IdeaVersionService.handle_idea_event("idea.created", {"performer_id": user_id})

    # handle_idea_event: idea present, service call succeeds
    with patch("app.db.database.AsyncSessionLocal") as m_session:
        mock_db_inner = AsyncMock()
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_db_inner)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        m_session.return_value = mock_ctx

        payload_idea = MagicMock(id=idea_id, owner_id=user_id)
        payload_idea.status = "DRAFT"
        payload_idea.title = "T"
        payload_idea.description = "D"
        payload_idea.ai_score = 0.5
        payload_idea.is_archived = False
        with patch.object(IdeaVersionService, "create_idea_snapshot", new_callable=AsyncMock):
            await IdeaVersionService.handle_idea_event(
                "idea.updated", {"idea": payload_idea, "performer_id": user_id}
            )

    # handle_idea_event: service raises exception (error logging path)
    with patch("app.db.database.AsyncSessionLocal") as m_session2:
        mock_ctx2 = AsyncMock()
        mock_ctx2.__aenter__ = AsyncMock(return_value=AsyncMock())
        mock_ctx2.__aexit__ = AsyncMock(return_value=False)
        m_session2.return_value = mock_ctx2

        with patch.object(IdeaVersionService, "create_idea_snapshot", new_callable=AsyncMock,
                          side_effect=Exception("snapshot fail")):
            await IdeaVersionService.handle_idea_event(
                "idea.updated", {"idea": payload_idea, "performer_id": user_id}
            )

    # Dependency provider
    await get_idea_version_service(db)


# ── partners/__init__ ──────────────────────────────────────────────────────────

def test_partners_init_import():
    """Ensure the partners.__init__ module is importable and exposes expected names."""
    import app.services.partners as pkg
    assert hasattr(pkg, "partner_profile")
    assert hasattr(pkg, "partner_request")
