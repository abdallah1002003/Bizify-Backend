import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import app.models as models
from app.core.security import get_password_hash
from app.models.enums import IdeaStatus, UserRole, ExperimentStatus
from app.services.ideation.idea_access import IdeaAccessService
from app.services.ideation import idea_metric
from app.services.ideation.idea_version import IdeaVersionService


class DummyModel:
    def __init__(self, **data):
        self._data = data

    def model_dump(self, exclude_unset: bool = True):
        _ = exclude_unset
        return dict(self._data)


async def _create_user(db, prefix: str) -> models.User:
    user = models.User(
        name=f"{prefix}-user",
        email=f"{prefix}_{uuid4().hex[:8]}@example.com",
        password_hash=get_password_hash("testpass123"),
        role=UserRole.ENTREPRENEUR,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _create_idea(db, owner_id, title: str) -> models.Idea:
    idea = models.Idea(
        owner_id=owner_id,
        title=title,
        description="test idea",
        status=IdeaStatus.DRAFT,
    )
    db.add(idea)
    await db.commit()
    await db.refresh(idea)
    return idea


@pytest.mark.asyncio
async def test_idea_access_crud_and_owner_filter(async_db):
    access_service = IdeaAccessService(async_db)
    
    owner = await _create_user(async_db, "owner")
    other_owner = await _create_user(async_db, "other_owner")
    collaborator = await _create_user(async_db, "collaborator")

    owner_idea = await _create_idea(async_db, owner.id, "Owner Idea")
    other_idea = await _create_idea(async_db, other_owner.id, "Other Idea")

    access_a = await access_service.create_idea_access(
        {"idea_id": owner_idea.id, "user_id": collaborator.id, "can_edit": True},
    )
    access_b = await access_service.create_idea_access(
        DummyModel(idea_id=other_idea.id, user_id=collaborator.id, can_edit=False),
    )

    assert (await access_service.get_idea_access(access_a.id)).id == access_a.id
    assert len(await access_service.get_idea_accesses(skip=0, limit=10)) == 2

    owner_accesses = await access_service.get_idea_accesses_by_owner(owner.id, skip=0, limit=10)
    assert len(owner_accesses) == 1
    assert owner_accesses[0].idea_id == owner_idea.id

    updated = await access_service.update_idea_access(access_a, {"can_delete": True, "unknown_field": "ignored"})
    assert updated.can_delete is True
    assert not hasattr(updated, "unknown_field")

    deleted = await access_service.delete_idea_access(access_b.id)
    assert deleted is not None
    assert await access_service.delete_idea_access(uuid4()) is None


@pytest.mark.asyncio
async def test_idea_version_crud_and_ordering(async_db):
    version_service = IdeaVersionService(async_db)
    owner = await _create_user(async_db, "version_owner")
    idea = await _create_idea(async_db, owner.id, "Versioned Idea")

    older = await version_service.create_idea_version(
        {
            "idea_id": idea.id,
            "created_by": owner.id,
            "snapshot_json": {"version": 1},
            "created_at": datetime.now(timezone.utc) - timedelta(days=2),
        },
    )
    newer = await version_service.create_idea_version(
        DummyModel(
            idea_id=idea.id,
            created_by=owner.id,
            snapshot_json={"version": 2},
            created_at=datetime.now(timezone.utc) - timedelta(days=1),
        ),
    )

    assert (await version_service.get_idea_version(older.id)).id == older.id
    ordered = await version_service.get_idea_versions(idea_id=idea.id, skip=0, limit=10)
    assert len(ordered) == 2
    assert ordered[0].id == newer.id
    assert ordered[1].id == older.id

    updated = await version_service.update_idea_version(older, {"snapshot_json": {"version": 1, "patched": True}})
    assert updated.snapshot_json["patched"] is True

    assert await version_service.delete_idea_version(uuid4()) is None
    assert await version_service.delete_idea_version(newer.id) is not None


@pytest.mark.asyncio
async def test_idea_metric_trends_ai_score_and_delete(async_db):
    owner = await _create_user(async_db, "metric_owner")
    idea = await _create_idea(async_db, owner.id, "Metric Idea")

    # record first metric
    first = await idea_metric.record_metric(async_db, idea.id, "quality", 10.0, "MANUAL", owner.id)
    # allow flexible matching for current (float vs int)
    single_trend = await idea_metric.get_metric_trends(async_db, idea.id, "quality")
    assert float(single_trend["current"]) == 10.0
    assert single_trend["trend"] == "stable"

    second = await idea_metric.record_metric(async_db, idea.id, "quality", 15.5, "MANUAL", owner.id)
    two_point_trend = await idea_metric.get_metric_trends(async_db, idea.id, "quality")
    assert float(two_point_trend["current"]) == 15.5
    assert two_point_trend["trend"] == "improving"
    assert float(two_point_trend["delta"]) == 5.5

    ai_metric = await idea_metric.create_idea_metric(
        async_db,
        DummyModel(
            idea_id=idea.id,
            created_by=owner.id,
            name="ai_score",
            value=0.88,
            type="AI_ANALYSIS",
        ),
    )
    await async_db.refresh(idea)
    assert float(idea.ai_score) == 0.88
    assert (await idea_metric.get_idea_metric(async_db, ai_metric.id)).id == ai_metric.id

    updated = await idea_metric.update_idea_metric(async_db, first, {"value": 9.0})
    assert float(updated.value) == 9.0
    assert len(await idea_metric.get_idea_metrics(async_db, idea_id=idea.id, skip=0, limit=10)) == 3

    deleted = await idea_metric.delete_idea_metric(async_db, second.id)
    assert deleted is not None
    assert await idea_metric.delete_idea_metric(async_db, uuid4()) is None


@pytest.mark.asyncio
async def test_idea_experiment_crud(async_db):
    from app.services.ideation import idea_experiment
    from app.services.ideation.idea_access import IdeaAccessService
    
    owner = await _create_user(async_db, "exp_owner")
    other = await _create_user(async_db, "exp_other")
    idea = await _create_idea(async_db, owner.id, "Experiment Idea")
    
    # Give owner access since initiate_experiment checks it
    access_svc = IdeaAccessService(async_db)
    await access_svc.create_idea_access(DummyModel(
        idea_id=idea.id,
        user_id=owner.id,
        can_edit=True,
        can_delete=True
    ))
    
    # 1. initiate_experiment (fail auth)
    with pytest.raises(PermissionError, match="Not authorized"):
        await idea_experiment.initiate_experiment(async_db, idea.id, "Test hyp", other.id)
        
    # 2. initiate_experiment (success)
    exp = await idea_experiment.initiate_experiment(async_db, idea.id, "Test hyp", owner.id)
    assert exp is not None
    assert exp.hypothesis == "Test hyp"
    assert exp.status == ExperimentStatus.RUNNING
    
    # 3. get_experiment
    found = await idea_experiment.get_experiment(async_db, exp.id)
    assert found is not None
    assert found.id == exp.id
    
    # 4. get_experiments
    exps = await idea_experiment.get_experiments(async_db, idea_id=idea.id, skip=0, limit=10)
    assert len(exps) >= 1
    
    # 5. create_experiment (raw)
    raw_exp = await idea_experiment.create_experiment(async_db, {"idea_id": idea.id, "created_by": owner.id, "hypothesis": "Raw hyp", "status": ExperimentStatus.RUNNING})
    assert raw_exp.hypothesis == "Raw hyp"
    
    # 6. update_experiment
    updated = await idea_experiment.update_experiment(async_db, exp, {"status": ExperimentStatus.FAILED})
    assert updated.status == ExperimentStatus.FAILED
    
    # 7. finalize_experiment (success)
    # this should change idea status to VALIDATED
    final = await idea_experiment.finalize_experiment(async_db, exp.id, {"conversion_rate": 0.5}, ExperimentStatus.COMPLETED)
    assert final.status == ExperimentStatus.COMPLETED
    assert float(final.result_summary["conversion_rate"]) == 0.5
    
    await async_db.refresh(idea)
    assert idea.status == IdeaStatus.VALIDATED
    
    # finalize non-existent
    assert await idea_experiment.finalize_experiment(async_db, uuid4(), {}, ExperimentStatus.COMPLETED) is None
    
    # 8. delete_experiment
    deleted = await idea_experiment.delete_experiment(async_db, exp.id)
    assert deleted is not None
    assert await idea_experiment.delete_experiment(async_db, uuid4()) is None
