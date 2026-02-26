import pytest
from datetime import datetime, timedelta, timezone
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


async def _create_business(db, owner_id) -> models.Business:
    business = models.Business(owner_id=owner_id, stage=BusinessStage.EARLY)
    db.add(business)
    await db.commit()
    await db.refresh(business)
    return business


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
async def test_file_service_crud_and_alias(async_db):
    owner = await _create_user(async_db, "file_owner")

    created = await file_service.create_file(
        async_db,
        {
            "owner_id": owner.id,
            "file_path": "/tmp/doc-a.txt",
            "file_type": "text/plain",
            "size": 120,
        },
    )
    assert created.id is not None
    assert (await file_service.get_file(async_db, created.id)).id == created.id

    alias_created = await file_service.create_file_record(
        async_db,
        DummyModel(
            owner_id=owner.id,
            file_path="/tmp/doc-b.pdf",
            file_type="application/pdf",
            size=300,
        ),
    )
    assert alias_created.file_type == "application/pdf"

    owner_files = await file_service.get_files(async_db, owner_id=owner.id)
    assert len(owner_files) == 2
    assert len(await file_service.get_files(async_db, skip=0, limit=1)) == 1

    updated = await file_service.update_file(async_db, created, {"file_type": "text/markdown", "missing_field": "ignored"})
    assert updated.file_type == "text/markdown"
    assert not hasattr(updated, "missing_field")

    deleted = await file_service.delete_file(async_db, created.id)
    assert deleted is not None
    assert await file_service.delete_file(async_db, uuid4()) is None


@pytest.mark.asyncio
async def test_notification_service_crud_and_alias(async_db):
    user_a = await _create_user(async_db, "notif_a")
    user_b = await _create_user(async_db, "notif_b")

    first = await notification_service.create_notification(
        async_db,
        {"user_id": user_a.id, "title": "A", "message": "hello"},
    )
    second = await notification_service.emit_notification(
        async_db,
        DummyModel(user_id=user_b.id, title="B", message="world"),
    )

    assert (await notification_service.get_notification(async_db, first.id)).id == first.id
    assert len(await notification_service.get_notifications(async_db, user_id=user_a.id)) == 1
    assert len(await notification_service.get_notifications(async_db, skip=0, limit=10)) >= 2

    updated = await notification_service.update_notification(
        async_db,
        first,
        {"is_read": True, "does_not_exist": True},
    )
    assert updated.is_read is True
    assert not hasattr(updated, "does_not_exist")

    deleted = await notification_service.delete_notification(async_db, second.id)
    assert deleted is not None
    assert await notification_service.delete_notification(async_db, uuid4()) is None


@pytest.mark.asyncio
async def test_share_link_service_crud_and_validation(async_db):
    creator = await _create_user(async_db, "share_creator")
    business = await _create_business(async_db, creator.id)
    idea = await _create_idea(async_db, creator.id, "share idea")

    generated_token_link = await share_link_service.create_share_link(
        async_db,
        DummyModel(created_by=creator.id, business_id=business.id, idea_id=idea.id, is_public=False),
    )
    assert generated_token_link.token

    explicit_link = await share_link_service.create_share_link(
        async_db,
        business_id=business.id,
        idea_id=idea.id,
        creator_id=creator.id,
        expires_in_days=2,
    )
    assert explicit_link.created_by == creator.id

    assert (await share_link_service.get_share_link(async_db, explicit_link.id)).id == explicit_link.id
    assert len(await share_link_service.get_share_links(async_db, created_by=creator.id)) == 2
    assert len(await share_link_service.get_share_links(async_db, skip=0, limit=1)) == 1

    updated = await share_link_service.update_share_link(async_db, explicit_link, {"is_public": True})
    assert updated.is_public is True

    assert (await share_link_service.validate_share_link(async_db, explicit_link.token)).id == explicit_link.id
    assert await share_link_service.validate_share_link(async_db, "missing-token") is None

    explicit_link.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    async_db.add(explicit_link)
    await async_db.commit()
    await async_db.refresh(explicit_link)
    assert await share_link_service.validate_share_link(async_db, explicit_link.token) is None

    deleted = await share_link_service.delete_share_link(async_db, generated_token_link.id)
    assert deleted is not None
    assert await share_link_service.delete_share_link(async_db, uuid4()) is None


@pytest.mark.asyncio
async def test_core_service_crud_aliases_and_status(async_db):
    owner = await _create_user(async_db, "core_owner")
    viewer = await _create_user(async_db, "core_viewer")

    file_obj = await core_service.create_file(
        async_db,
        {"owner_id": owner.id, "file_path": "/tmp/core.txt", "file_type": "text/plain", "size": 64},
    )
    alias_file = await core_service.create_file_record(
        async_db,
        DummyModel(owner_id=owner.id, file_path="/tmp/core-2.txt", file_type="text/plain", size=65),
    )
    assert alias_file.id is not None
    assert (await core_service.get_file(async_db, file_obj.id)).id == file_obj.id
    assert len(await core_service.get_files(async_db, owner_id=owner.id)) == 2
    assert len(await core_service.get_files(async_db, skip=0, limit=1)) == 1

    updated_file = await core_service.update_file(async_db, file_obj, {"file_path": "/tmp/core-updated.txt", "ignore_me": True})
    assert updated_file.file_path == "/tmp/core-updated.txt"

    first_notification = await core_service.create_notification(
        async_db,
        {"user_id": owner.id, "title": "Core A", "message": "a"},
    )
    second_notification = await core_service.emit_notification(
        async_db,
        DummyModel(user_id=viewer.id, title="Core B", message="b"),
    )
    assert second_notification.id is not None
    assert (await core_service.get_notification(async_db, first_notification.id)).id == first_notification.id
    assert len(await core_service.get_notifications(async_db, user_id=owner.id)) == 1
    assert len(await core_service.get_notifications(async_db, skip=0, limit=10)) >= 2

    updated_notification = await core_service.update_notification(async_db, first_notification, {"is_read": True})
    assert updated_notification.is_read is True

    assert await core_service.delete_notification(async_db, uuid4()) is None
    assert await core_service.delete_file(async_db, uuid4()) is None

    assert await core_service.delete_notification(async_db, second_notification.id) is not None
    assert await core_service.delete_file(async_db, alias_file.id) is not None

    status = await core_service.get_detailed_status()
    assert status["module"] == "core_service"
    assert status["status"] == "operational"
    assert "timestamp" in status

    await core_service.reset_internal_state()

