"""Tests for core services (file, notification, share_link) and ideation/idea_access."""
import pytest
from unittest.mock import AsyncMock, MagicMock
import uuid
from datetime import datetime, timezone, timedelta

from app.services.core.file_service import FileService, get_file_service
from app.services.core.notification_service import NotificationService, get_notification_service
from app.services.core.share_link_service import ShareLinkService, get_share_link_service, _is_expired
from app.services.ideation.idea_access import IdeaAccessService, get_idea_access_service


# ── FileService ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_file_service_exhaustive():
    db = AsyncMock()
    svc = FileService(db=db)
    svc.repo = AsyncMock()
    uid = uuid.uuid4()
    owner_id = uuid.uuid4()

    # get_file
    await svc.get_file(uid)

    # get_files: with owner_id
    await svc.get_files(owner_id=owner_id)

    # get_files: without filter
    await svc.get_files()

    # create_file
    await svc.create_file({"filename": "test.pdf", "owner_id": owner_id})

    # update_file
    await svc.update_file(MagicMock(), {"filename": "updated.pdf"})

    # delete_file: found
    svc.repo.get.return_value = MagicMock()
    await svc.delete_file(uid)

    # delete_file: not found
    svc.repo.get.return_value = None
    assert await svc.delete_file(uid) is None

    # Dependency provider
    await get_file_service(db)


# ── NotificationService ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_notification_service_exhaustive():
    db = AsyncMock()
    svc = NotificationService(db=db)
    svc.repo = AsyncMock()
    uid = uuid.uuid4()
    user_id = uuid.uuid4()

    # get_notification
    await svc.get_notification(uid)

    # get_notifications: with user_id filter
    svc.repo.get_for_user.return_value = [MagicMock(), MagicMock()]
    await svc.get_notifications(user_id=user_id)

    # get_notifications: no filter
    await svc.get_notifications()

    # create / update / delete
    await svc.create_notification({"user_id": user_id, "message": "hello"})
    await svc.update_notification(MagicMock(), {"message": "updated"})
    await svc.delete_notification(uid)

    # Dependency provider
    await get_notification_service(db)


# ── ShareLinkService ───────────────────────────────────────────────────────────

def test_is_expired_naive():
    """_is_expired strips timezone from 'now' when expires_at is naive."""
    naive_past = datetime(2000, 1, 1)  # no tzinfo
    assert _is_expired(naive_past) is True

    naive_future = datetime(2099, 1, 1)
    assert _is_expired(naive_future) is False


@pytest.mark.asyncio
async def test_share_link_service_exhaustive():
    db = AsyncMock()
    svc = ShareLinkService(db=db)
    svc.repo = AsyncMock()
    uid = uuid.uuid4()
    creator_id = uuid.uuid4()
    biz_id = uuid.uuid4()

    # get_share_link
    await svc.get_share_link(uid)

    # get_share_links: with creator filter
    svc.repo.get_all.return_value = [
        MagicMock(created_by=creator_id),
        MagicMock(created_by=uuid.uuid4()),  # different owner
    ]
    result = await svc.get_share_links(created_by=creator_id)
    assert len(result) == 1

    # get_share_links: no filter
    await svc.get_share_links()

    # create_share_link: from obj_in dict (token already present)
    await svc.create_share_link(obj_in={"business_id": biz_id, "token": "tok"})

    # create_share_link: from obj_in dict WITHOUT token → autogen
    await svc.create_share_link(obj_in={"business_id": biz_id})

    # create_share_link: from keyword args
    await svc.create_share_link(business_id=biz_id, idea_id=None, creator_id=creator_id)

    # update / delete
    await svc.update_share_link(MagicMock(), {"is_public": True})
    await svc.delete_share_link(uid)

    # validate_share_link: not found
    svc.repo.get_by_token.return_value = None
    assert await svc.validate_share_link("bad_token") is None

    # validate_share_link: found, not expired
    future = datetime.now(timezone.utc) + timedelta(days=7)
    svc.repo.get_by_token.return_value = MagicMock(expires_at=future)
    result = await svc.validate_share_link("good_token")
    assert result is not None

    # validate_share_link: found, expired
    past = datetime.now(timezone.utc) - timedelta(days=1)
    svc.repo.get_by_token.return_value = MagicMock(expires_at=past)
    assert await svc.validate_share_link("expired_token") is None

    # validate_share_link: found, expires_at is None
    svc.repo.get_by_token.return_value = MagicMock(expires_at=None)
    result = await svc.validate_share_link("no_expiry_token")
    assert result is not None

    # Dependency provider
    await get_share_link_service(db)


# ── IdeaAccessService ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_idea_access_service_exhaustive():
    db = AsyncMock()
    svc = IdeaAccessService(db=db)
    svc.repo = AsyncMock()
    svc.idea_repo = AsyncMock()
    uid = uuid.uuid4()
    idea_id = uuid.uuid4()
    user_id = uuid.uuid4()

    # check_idea_access: idea not found
    svc.idea_repo.get.return_value = None
    assert await svc.check_idea_access(idea_id, user_id) is False

    # check_idea_access: user is owner
    svc.idea_repo.get.return_value = MagicMock(owner_id=user_id)
    assert await svc.check_idea_access(idea_id, user_id) is True

    # check_idea_access: no access record
    svc.idea_repo.get.return_value = MagicMock(owner_id=uuid.uuid4())
    svc.repo.get_by_idea_and_user.return_value = None
    assert await svc.check_idea_access(idea_id, user_id) is False

    # check_idea_access: view perm
    mock_access = MagicMock(can_edit=True, can_delete=True, can_experiment=True)
    svc.repo.get_by_idea_and_user.return_value = mock_access
    assert await svc.check_idea_access(idea_id, user_id, "view") is True

    # check_idea_access: edit perm
    assert await svc.check_idea_access(idea_id, user_id, "edit") is True
    mock_access.can_edit = False
    assert await svc.check_idea_access(idea_id, user_id, "edit") is False

    # check_idea_access: delete perm
    mock_access.can_delete = True
    assert await svc.check_idea_access(idea_id, user_id, "delete") is True

    # check_idea_access: experiment perm
    mock_access.can_experiment = True
    assert await svc.check_idea_access(idea_id, user_id, "experiment") is True

    # check_idea_access: unknown perm → False
    assert await svc.check_idea_access(idea_id, user_id, "unknown_perm") is False

    # grant_access: existing access → update
    svc.repo.get_by_idea_and_user.return_value = mock_access
    await svc.grant_access(idea_id, user_id, {"edit": True, "delete": True, "experiment": False})

    # grant_access: no existing → create_safe succeeds
    svc.repo.get_by_idea_and_user.return_value = None
    svc.repo.create_safe.return_value = MagicMock()
    await svc.grant_access(idea_id, user_id, {"edit": True})

    # grant_access: create_safe returns None, re-fetch succeeds
    svc.repo.create_safe.return_value = None
    svc.repo.get_by_idea_and_user.side_effect = [None, mock_access]
    await svc.grant_access(idea_id, user_id, {"edit": True})
    svc.repo.get_by_idea_and_user.side_effect = None

    # grant_access: create_safe None AND re-fetch None → RuntimeError
    svc.repo.create_safe.return_value = None
    svc.repo.get_by_idea_and_user.return_value = None
    with pytest.raises(RuntimeError):
        await svc.grant_access(idea_id, user_id, {"edit": True})

    # Basic CRUD
    await svc.get_idea_access(uid)
    await svc.get_idea_accesses()
    await svc.get_idea_accesses_by_owner(user_id)

    # create_idea_access: create_safe succeeds
    svc.repo.create_safe.return_value = MagicMock()
    await svc.create_idea_access({"idea_id": idea_id, "user_id": user_id})

    # create_idea_access: create_safe None → existing found
    svc.repo.create_safe.return_value = None
    svc.repo.get_by_idea_and_user.return_value = MagicMock()
    await svc.create_idea_access({"idea_id": idea_id, "user_id": user_id})

    # create_idea_access: create_safe None AND existing None → RuntimeError
    svc.repo.create_safe.return_value = None
    svc.repo.get_by_idea_and_user.return_value = None
    with pytest.raises(RuntimeError):
        await svc.create_idea_access({"idea_id": idea_id, "user_id": user_id})

    # update / delete
    await svc.update_idea_access(MagicMock(), {"can_edit": False})
    await svc.delete_idea_access(uid)

    # Dependency provider
    await get_idea_access_service(db)
