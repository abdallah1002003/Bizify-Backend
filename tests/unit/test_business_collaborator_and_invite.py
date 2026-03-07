"""Tests for BusinessCollaboratorService and BusinessInviteService."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import uuid
from datetime import datetime, timezone, timedelta

from app.models.enums import CollaboratorRole, InviteStatus
from app.services.business.business_collaborator import (
    BusinessCollaboratorService, get_business_collaborator_service,
    register_business_collaborator_handlers
)
from app.services.business.business_invite import (
    BusinessInviteService
)


# ── BusinessCollaboratorService ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_business_collaborator_service_exhaustive():
    db = AsyncMock()
    svc = BusinessCollaboratorService(db)
    svc.repo = AsyncMock()
    uid = uuid.uuid4()
    business_id = uuid.uuid4()
    user_id = uuid.uuid4()

    # get queries
    await svc.get_collaborator(uid)
    await svc.get_business_collaborator(uid)
    await svc.get_collaborators(business_id)
    await svc.get_business_collaborators()

    # add_collaborator
    await svc.add_collaborator(business_id, user_id, CollaboratorRole.EDITOR)
    svc.repo.upsert.assert_called_with(business_id, user_id, CollaboratorRole.EDITOR)

    # create_business_collaborator
    await svc.create_business_collaborator({
        "business_id": business_id,
        "user_id": user_id,
        "role": CollaboratorRole.VIEWER
    })
    svc.repo.upsert.assert_called_with(business_id, user_id, CollaboratorRole.VIEWER)

    # update_business_collaborator
    await svc.update_business_collaborator(MagicMock(), {"role": CollaboratorRole.EDITOR})
    svc.repo.update.assert_called()

    # remove_collaborator: not found
    svc.repo.get_by_business_and_user.return_value = None
    assert await svc.remove_collaborator(business_id, user_id) is None

    # remove_collaborator: owner
    svc.repo.get_by_business_and_user.return_value = MagicMock(role=CollaboratorRole.OWNER)
    with pytest.raises(PermissionError, match="Cannot remove owner"):
        await svc.remove_collaborator(business_id, user_id)

    # remove_collaborator: success
    mock_existing = MagicMock(id=uid, role=CollaboratorRole.EDITOR)
    svc.repo.get_by_business_and_user.return_value = mock_existing
    await svc.remove_collaborator(business_id, user_id)
    svc.repo.delete.assert_called_with(uid)

    # delete_business_collaborator: not found
    svc.repo.get.return_value = None
    assert await svc.delete_business_collaborator(uid) is None

    # delete_business_collaborator: owner
    svc.repo.get.return_value = MagicMock(role=CollaboratorRole.OWNER)
    with pytest.raises(PermissionError, match="Cannot remove owner"):
        await svc.delete_business_collaborator(uid)

    # delete_business_collaborator: success
    svc.repo.get.return_value = mock_existing
    await svc.delete_business_collaborator(uid)
    svc.repo.delete.assert_called_with(uid)

    # handle_business_event
    register_business_collaborator_handlers()

    await BusinessCollaboratorService.handle_business_event("ev", {})

    with patch("app.db.database.AsyncSessionLocal") as m_session:
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=AsyncMock())
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        m_session.return_value = mock_ctx

        b_mock = MagicMock(id=business_id, owner_id=user_id)
        with patch.object(BusinessCollaboratorService, "add_collaborator", new_callable=AsyncMock):
            await BusinessCollaboratorService.handle_business_event(
                "business.created", {"business": b_mock}
            )

    # handle_business_event: exception
    with patch("app.db.database.AsyncSessionLocal") as m_session2:
        mock_ctx2 = AsyncMock()
        mock_ctx2.__aenter__ = AsyncMock(return_value=AsyncMock())
        mock_ctx2.__aexit__ = AsyncMock(return_value=False)
        m_session2.return_value = mock_ctx2

        with patch.object(BusinessCollaboratorService, "add_collaborator", 
                          new_callable=AsyncMock, side_effect=Exception("DB fail")):
            await BusinessCollaboratorService.handle_business_event(
                "business.created", {"business": b_mock}
            )

    # dependency provider
    await get_business_collaborator_service(db)


# ── BusinessInviteService ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_business_invite_service_exhaustive():
    db = AsyncMock()
    svc = BusinessInviteService(db)
    svc.invite_repo = AsyncMock()
    svc.user_repo = AsyncMock()
    svc.invite_idea_repo = AsyncMock()
    
    uid = uuid.uuid4()
    business_id = uuid.uuid4()
    user_id = uuid.uuid4()

    # get queries
    await svc.get_invite(uid)
    await svc.get_business_invite(uid)
    await svc.get_invites(business_id)
    await svc.get_business_invites()

    # create_invite (direct)
    await svc.create_invite(business_id, "test@test.com", user_id)
    svc.invite_repo.create.assert_called()

    # create_business_invite (from obj)
    await svc.create_business_invite({"email": "a@b.com", "business_id": business_id})
    svc.invite_repo.create.assert_called()

    # create_business_invite (obj has token)
    await svc.create_business_invite({"email": "a@b.com", "business_id": business_id, "token": "tok"})

    # update_business_invite: not changing to accepted
    db_obj = MagicMock(status=InviteStatus.PENDING)
    updated_pending = MagicMock(status=InviteStatus.PENDING)
    svc.invite_repo.update.return_value = updated_pending
    await svc.update_business_invite(db_obj, {"status": "PENDING"})

    # update_business_invite: changing to accepted, user found -> adds collaborator
    updated_accepted = MagicMock(status=InviteStatus.ACCEPTED, email="u@t.com", business_id=business_id)
    svc.invite_repo.update.return_value = updated_accepted
    svc.user_repo.get_by_email.return_value = MagicMock(id=user_id)
    with patch("app.services.business.business_collaborator.BusinessCollaboratorService.add_collaborator", new_callable=AsyncMock) as mock_add_collab:
        await svc.update_business_invite(db_obj, {"status": "ACCEPTED"})
        mock_add_collab.assert_called_with(business_id, user_id, CollaboratorRole.VIEWER)

    # update_business_invite: changing to accepted, user not found
    svc.user_repo.get_by_email.return_value = None
    with patch("app.services.business.business_collaborator.BusinessCollaboratorService.add_collaborator", new_callable=AsyncMock) as mock_add_collab2:
        await svc.update_business_invite(db_obj, {"status": "ACCEPTED"})
        mock_add_collab2.assert_not_called()

    # update_business_invite: already accepted
    db_obj_acc = MagicMock(status=InviteStatus.ACCEPTED)
    svc.invite_repo.update.return_value = updated_accepted
    await svc.update_business_invite(db_obj_acc, {"status": "ACCEPTED"})

    # delete_business_invite
    svc.invite_repo.get.return_value = db_obj
    svc.invite_repo.delete.return_value = db_obj
    await svc.delete_business_invite(uid)
    
    svc.invite_repo.get.return_value = None
    assert await svc.delete_business_invite(uid) is None

    # accept_invite: token not found
    svc.invite_repo.get_by_token.return_value = None
    assert await svc.accept_invite("tok", user_id) is False

    # accept_invite: not pending
    svc.invite_repo.get_by_token.return_value = MagicMock(status=InviteStatus.ACCEPTED)
    assert await svc.accept_invite("tok", user_id) is False

    from app.core.crud_utils import _utc_now

    # accept_invite: expired
    past = _utc_now() - timedelta(days=1)
    svc.invite_repo.get_by_token.return_value = MagicMock(status=InviteStatus.PENDING, expires_at=past)
    assert await svc.accept_invite("tok", user_id) is False
    svc.invite_repo.update.assert_called_with(svc.invite_repo.get_by_token.return_value, {"status": InviteStatus.EXPIRED})

    # accept_invite: success
    future = _utc_now() + timedelta(days=1)
    mock_invite = MagicMock(status=InviteStatus.PENDING, expires_at=future, business_id=business_id)
    svc.invite_repo.get_by_token.return_value = mock_invite
    with patch("app.services.business.business_collaborator.BusinessCollaboratorService.add_collaborator", new_callable=AsyncMock) as mock_add_collab3:
        assert await svc.accept_invite("tok", user_id) is True
        svc.invite_repo.update.assert_called_with(mock_invite, {"status": InviteStatus.ACCEPTED})
        mock_add_collab3.assert_called_with(business_id, user_id, CollaboratorRole.EDITOR)


    # ── BusinessInviteIdea
    await svc.get_business_invite_idea(uid)
    await svc.get_business_invite_ideas()
    await svc.create_business_invite_idea({"invite_id": uid})
    await svc.update_business_invite_idea(MagicMock(), {"idea_id": uid})

    svc.invite_idea_repo.get.return_value = db_obj
    await svc.delete_business_invite_idea(uid)
    
    svc.invite_idea_repo.get.return_value = None
    assert await svc.delete_business_invite_idea(uid) is None
