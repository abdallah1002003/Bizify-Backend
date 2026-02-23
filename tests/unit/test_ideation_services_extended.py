from datetime import datetime, timedelta
from uuid import uuid4

import app.models as models
from app.core.security import get_password_hash
from app.models.enums import IdeaStatus, UserRole
from app.services.ideation import idea_access, idea_metric, idea_version


class DummyModel:
    def __init__(self, **data):
        self._data = data

    def model_dump(self, exclude_unset: bool = True):
        _ = exclude_unset
        return dict(self._data)


def _create_user(db, prefix: str) -> models.User:
    user = models.User(
        name=f"{prefix}-user",
        email=f"{prefix}_{uuid4().hex[:8]}@example.com",
        password_hash=get_password_hash("testpass123"),
        role=UserRole.ENTREPRENEUR,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_idea(db, owner_id, title: str) -> models.Idea:
    idea = models.Idea(
        owner_id=owner_id,
        title=title,
        description="test idea",
        status=IdeaStatus.DRAFT,
    )
    db.add(idea)
    db.commit()
    db.refresh(idea)
    return idea


def test_idea_access_crud_and_owner_filter(db):
    owner = _create_user(db, "owner")
    other_owner = _create_user(db, "other_owner")
    collaborator = _create_user(db, "collaborator")

    owner_idea = _create_idea(db, owner.id, "Owner Idea")
    other_idea = _create_idea(db, other_owner.id, "Other Idea")

    access_a = idea_access.create_idea_access(
        db,
        {"idea_id": owner_idea.id, "user_id": collaborator.id, "can_edit": True},
    )
    access_b = idea_access.create_idea_access(
        db,
        DummyModel(idea_id=other_idea.id, user_id=collaborator.id, can_edit=False),
    )

    assert idea_access.get_idea_access(db, access_a.id).id == access_a.id
    assert len(idea_access.get_idea_accesses(db, skip=0, limit=10)) == 2

    owner_accesses = idea_access.get_idea_accesses_by_owner(db, owner.id, skip=0, limit=10)
    assert len(owner_accesses) == 1
    assert owner_accesses[0].idea_id == owner_idea.id

    updated = idea_access.update_idea_access(db, access_a, {"can_delete": True, "unknown_field": "ignored"})
    assert updated.can_delete is True
    assert not hasattr(updated, "unknown_field")

    deleted = idea_access.delete_idea_access(db, access_b.id)
    assert deleted is not None
    assert idea_access.delete_idea_access(db, uuid4()) is None


def test_idea_version_crud_and_ordering(db):
    owner = _create_user(db, "version_owner")
    idea = _create_idea(db, owner.id, "Versioned Idea")

    older = idea_version.create_idea_version(
        db,
        {
            "idea_id": idea.id,
            "created_by": owner.id,
            "snapshot_json": {"version": 1},
            "created_at": datetime.utcnow() - timedelta(days=2),
        },
    )
    newer = idea_version.create_idea_version(
        db,
        DummyModel(
            idea_id=idea.id,
            created_by=owner.id,
            snapshot_json={"version": 2},
            created_at=datetime.utcnow() - timedelta(days=1),
        ),
    )

    assert idea_version.get_idea_version(db, older.id).id == older.id
    ordered = idea_version.get_idea_versions(db, idea_id=idea.id, skip=0, limit=10)
    assert len(ordered) == 2
    assert ordered[0].id == newer.id
    assert ordered[1].id == older.id

    updated = idea_version.update_idea_version(db, older, {"snapshot_json": {"version": 1, "patched": True}})
    assert updated.snapshot_json["patched"] is True

    assert idea_version.delete_idea_version(db, uuid4()) is None
    assert idea_version.delete_idea_version(db, newer.id) is not None


def test_idea_metric_trends_ai_score_and_delete(db):
    owner = _create_user(db, "metric_owner")
    idea = _create_idea(db, owner.id, "Metric Idea")

    empty_trend = idea_metric.get_metric_trends(db, idea.id, "quality")
    assert empty_trend == {"current": 0, "trend": "stable", "delta": 0}

    first = idea_metric.record_metric(db, idea.id, "quality", 10.0, "MANUAL", owner.id)
    single_trend = idea_metric.get_metric_trends(db, idea.id, "quality")
    assert single_trend == {"current": 10.0, "trend": "stable", "delta": 0}

    second = idea_metric.record_metric(db, idea.id, "quality", 15.5, "MANUAL", owner.id)
    two_point_trend = idea_metric.get_metric_trends(db, idea.id, "quality")
    assert two_point_trend["current"] == 15.5
    assert two_point_trend["trend"] == "improving"
    assert two_point_trend["delta"] == 5.5

    ai_metric = idea_metric.create_idea_metric(
        db,
        DummyModel(
            idea_id=idea.id,
            created_by=owner.id,
            name="ai_score",
            value=0.88,
            type="AI_ANALYSIS",
        ),
    )
    db.refresh(idea)
    assert idea.ai_score == 0.88
    assert idea_metric.get_idea_metric(db, ai_metric.id).id == ai_metric.id

    updated = idea_metric.update_idea_metric(db, first, {"value": 9.0})
    assert updated.value == 9.0
    assert len(idea_metric.get_idea_metrics(db, idea_id=idea.id, skip=0, limit=10)) == 3

    deleted = idea_metric.delete_idea_metric(db, second.id)
    assert deleted is not None
    assert idea_metric.delete_idea_metric(db, uuid4()) is None

