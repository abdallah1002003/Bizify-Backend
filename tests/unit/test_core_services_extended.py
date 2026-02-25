from datetime import datetime, timedelta
from uuid import uuid4

import app.models as models
from app.core.security import get_password_hash
from app.models.enums import BusinessStage, IdeaStatus, UserRole
from app.services.core import core_service, file_service, notification_service, share_link_service


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


def _create_business(db, owner_id) -> models.Business:
    business = models.Business(owner_id=owner_id, stage=BusinessStage.EARLY)
    db.add(business)
    db.commit()
    db.refresh(business)
    return business


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


def test_file_service_crud_and_alias(db):
    owner = _create_user(db, "file_owner")

    created = file_service.create_file(
        db,
        {
            "owner_id": owner.id,
            "file_path": "/tmp/doc-a.txt",
            "file_type": "text/plain",
            "size": 120,
        },
    )
    assert created.id is not None
    assert file_service.get_file(db, created.id).id == created.id

    alias_created = file_service.create_file_record(
        db,
        DummyModel(
            owner_id=owner.id,
            file_path="/tmp/doc-b.pdf",
            file_type="application/pdf",
            size=300,
        ),
    )
    assert alias_created.file_type == "application/pdf"

    owner_files = file_service.get_files(db, owner_id=owner.id)
    assert len(owner_files) == 2
    assert len(file_service.get_files(db, skip=0, limit=1)) == 1

    updated = file_service.update_file(db, created, {"file_type": "text/markdown", "missing_field": "ignored"})
    assert updated.file_type == "text/markdown"
    assert not hasattr(updated, "missing_field")

    deleted = file_service.delete_file(db, created.id)
    assert deleted is not None
    assert file_service.delete_file(db, uuid4()) is None


def test_notification_service_crud_and_alias(db):
    user_a = _create_user(db, "notif_a")
    user_b = _create_user(db, "notif_b")

    first = notification_service.create_notification(
        db,
        {"user_id": user_a.id, "title": "A", "message": "hello"},
    )
    second = notification_service.emit_notification(
        db,
        DummyModel(user_id=user_b.id, title="B", message="world"),
    )

    assert notification_service.get_notification(db, first.id).id == first.id
    assert len(notification_service.get_notifications(db, user_id=user_a.id)) == 1
    assert len(notification_service.get_notifications(db, skip=0, limit=10)) >= 2

    updated = notification_service.update_notification(
        db,
        first,
        {"is_read": True, "does_not_exist": True},
    )
    assert updated.is_read is True
    assert not hasattr(updated, "does_not_exist")

    deleted = notification_service.delete_notification(db, second.id)
    assert deleted is not None
    assert notification_service.delete_notification(db, uuid4()) is None


def test_share_link_service_crud_and_validation(db):
    creator = _create_user(db, "share_creator")
    business = _create_business(db, creator.id)
    idea = _create_idea(db, creator.id, "share idea")

    generated_token_link = share_link_service.create_share_link(
        db,
        DummyModel(created_by=creator.id, business_id=business.id, idea_id=idea.id, is_public=False),
    )
    assert generated_token_link.token

    explicit_link = share_link_service.create_share_link(
        db,
        business_id=business.id,
        idea_id=idea.id,
        creator_id=creator.id,
        expires_in_days=2,
    )
    assert explicit_link.created_by == creator.id

    assert share_link_service.get_share_link(db, explicit_link.id).id == explicit_link.id
    assert len(share_link_service.get_share_links(db, created_by=creator.id)) == 2
    assert len(share_link_service.get_share_links(db, skip=0, limit=1)) == 1

    updated = share_link_service.update_share_link(db, explicit_link, {"is_public": True})
    assert updated.is_public is True

    assert share_link_service.validate_share_link(db, explicit_link.token).id == explicit_link.id
    assert share_link_service.validate_share_link(db, "missing-token") is None

    explicit_link.expires_at = datetime.utcnow() - timedelta(days=1)
    db.add(explicit_link)
    db.commit()
    db.refresh(explicit_link)
    assert share_link_service.validate_share_link(db, explicit_link.token) is None

    deleted = share_link_service.delete_share_link(db, generated_token_link.id)
    assert deleted is not None
    assert share_link_service.delete_share_link(db, uuid4()) is None


def test_core_service_crud_aliases_and_status(db):
    owner = _create_user(db, "core_owner")
    viewer = _create_user(db, "core_viewer")
    business = _create_business(db, owner.id)
    idea = _create_idea(db, owner.id, "core idea")

    file_obj = core_service.create_file(
        db,
        {"owner_id": owner.id, "file_path": "/tmp/core.txt", "file_type": "text/plain", "size": 64},
    )
    alias_file = core_service.create_file_record(
        db,
        DummyModel(owner_id=owner.id, file_path="/tmp/core-2.txt", file_type="text/plain", size=65),
    )
    assert alias_file.id is not None
    assert core_service.get_file(db, file_obj.id).id == file_obj.id
    assert len(core_service.get_files(db, owner_id=owner.id)) == 2
    assert len(core_service.get_files(db, skip=0, limit=1)) == 1

    updated_file = core_service.update_file(db, file_obj, {"file_path": "/tmp/core-updated.txt", "ignore_me": True})
    assert updated_file.file_path == "/tmp/core-updated.txt"

    first_notification = core_service.create_notification(
        db,
        {"user_id": owner.id, "title": "Core A", "message": "a"},
    )
    second_notification = core_service.emit_notification(
        db,
        DummyModel(user_id=viewer.id, title="Core B", message="b"),
    )
    assert second_notification.id is not None
    assert core_service.get_notification(db, first_notification.id).id == first_notification.id
    assert len(core_service.get_notifications(db, user_id=owner.id)) == 1
    assert len(core_service.get_notifications(db, skip=0, limit=10)) >= 2

    updated_notification = core_service.update_notification(db, first_notification, {"is_read": True})
    assert updated_notification.is_read is True

    assert core_service.delete_notification(db, uuid4()) is None
    assert core_service.delete_file(db, uuid4()) is None

    assert core_service.delete_notification(db, second_notification.id) is not None
    assert core_service.delete_file(db, alias_file.id) is not None

    status = core_service.get_detailed_status()
    assert status["module"] == "core_service"
    assert status["status"] == "operational"
    assert "timestamp" in status

    core_service.reset_internal_state()

