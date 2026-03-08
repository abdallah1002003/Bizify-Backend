import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, timezone

import app.models as models
from app.models.enums import CollaboratorRole, InviteStatus, RoadmapStageStatus
from app.services.users import admin_log_service, user_profile
from app.services.business import (
    business_service,
    business_roadmap,
    business_collaborator,
    business_invite,
)

@pytest.mark.asyncio
class TestUserServicesCoverage:
    """Tests for AdminActionLog and UserProfile services."""

    async def test_admin_log_service_crud(self):
        db = AsyncMock()
        db.add = MagicMock()
        log_id = uuid.uuid4()
        
        # Test create
        payload = {"admin_id": uuid.uuid4(), "action_type": "TEST", "target_entity": "test", "target_id": uuid.uuid4()}
        await admin_log_service.create_admin_action_log(db, payload)
        db.add.assert_called()
        db.commit.assert_called()
        
        # Test update
        log_obj = models.AdminActionLog(id=log_id)
        await admin_log_service.update_admin_action_log(db, log_obj, {"action_type": "UPDATED"})
        assert log_obj.action_type == "UPDATED"
        
        # Test get
        db.get.return_value = log_obj
        result = await admin_log_service.get_admin_action_log(db, log_id)
        assert result.id == log_id
        
        # Test list
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = [result]
        db.execute.return_value = mock_result
        logs = await admin_log_service.get_admin_logs(db)
        assert len(logs) == 1
        
        # Test delete (found)
        await admin_log_service.delete_admin_action_log(db, log_id)
        db.delete.assert_called_once()
        
        # Test delete (not found)
        db.get.return_value = None
        res = await admin_log_service.delete_admin_action_log(db, uuid.uuid4())
        assert res is None

    async def test_user_profile_lifecycle(self):
        db = AsyncMock()
        db.add = MagicMock()
        user_id = uuid.uuid4()
        profile_id = uuid.uuid4()
        profile = models.UserProfile(id=profile_id, user_id=user_id, bio="Old bio")
        
        # Test get_user_profile (by id)
        db.get.return_value = profile
        res = await user_profile.get_user_profile(db, id=profile_id)
        assert res.id == profile_id
        
        # Test get_user_profile (by user_id)
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = profile
        mock_res.scalars().first.return_value = profile
        db.execute.return_value = mock_res
        res = await user_profile.get_user_profile(db, user_id=user_id)
        assert res.user_id == user_id
        
        # Test get_user_profiles (list)
        mock_list = MagicMock()
        mock_list.scalars().all.return_value = [profile]
        db.execute.return_value = mock_list
        res = await user_profile.get_user_profiles(db)
        assert len(res) == 1
        
        # Test create
        await user_profile.create_user_profile(db, {"user_id": user_id, "bio": "New"})
        db.add.assert_called()
        
        # Test update with admin logging
        admin_id = uuid.uuid4()
        await user_profile.update_user_profile(db, profile, {"bio": "Updated"}, performer_id=admin_id)
        assert profile.bio == "Updated"
        db.commit.assert_called()
        
        # Test update_by_user_id (existing)
        mock_update_res = MagicMock()
        mock_update_res.scalar_one_or_none.return_value = profile
        db.execute.return_value = mock_update_res
        await user_profile.update_user_profile_by_user_id(db, user_id, {"bio": "Updated Again"}, performer_id=admin_id)
        assert profile.bio == "Updated Again"
        
        # Test update_by_user_id (create new if missing)
        mock_missing_res = MagicMock()
        mock_missing_res.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_missing_res
        await user_profile.update_user_profile_by_user_id(db, uuid.uuid4(), {"bio": "Created on update"})
        db.add.assert_called()

        # Test delete
        db.get.return_value = profile
        await user_profile.delete_user_profile(db, profile_id)
        db.delete.assert_called()
        
        # Test delete missing
        db.get.return_value = None
        res = await user_profile.delete_user_profile(db, uuid.uuid4())
        assert res is None
        
        # Test admin logging error branch
        with pytest.raises(ValueError):
            await user_profile._record_admin_action(db, admin_id=admin_id, action_type="TEST", target_id=None)
            
        # Test get_user_profile with no args
        assert await user_profile.get_user_profile(db) is None

@pytest.mark.asyncio
class TestBusinessServicesCoverage:
    """Tests for Business, Roadmap, Collaborator and Invite services."""

    async def test_business_service_full(self):
        db = AsyncMock()
        db.add = MagicMock()
        roadmap_svc = AsyncMock() # Must be AsyncMock for await
        collab_svc = AsyncMock()
        svc = business_service.BusinessService(db, roadmap_service=roadmap_svc, collaborator_service=collab_svc)
        
        biz_id = uuid.uuid4()
        owner_id = uuid.uuid4()
        
        # Test create
        await svc.create_business({"owner_id": owner_id, "context_json": {}})
        roadmap_svc.init_default_roadmap.assert_called_once()
        db.commit.assert_called()
        
        # Test get
        mock_biz = models.Business(id=biz_id, owner_id=owner_id)
        db.execute.return_value = MagicMock(scalar_one_or_none=lambda: mock_biz)
        res = await svc.get_business(biz_id)
        assert res.id == biz_id
        
        # Test list
        mock_list = MagicMock()
        mock_list.scalars().all.return_value = [mock_biz]
        db.execute.return_value = mock_list
        res = await svc.get_businesses(owner_id=owner_id)
        assert len(res) == 1
        
        # Test update
        await svc.update_business(mock_biz, {"is_archived": True})
        assert mock_biz.is_archived is True
        
        # Test update stage
        db.execute.return_value = MagicMock(scalar_one_or_none=lambda: mock_biz)
        await svc.update_business_stage(biz_id, "Scale")
        assert mock_biz.stage == "Scale"
        
        # Test delete
        db.execute.return_value = MagicMock(scalar_one_or_none=lambda: mock_biz)
        await svc.delete_business(biz_id)
        db.delete.assert_called_once()

    async def test_business_roadmap_logic(self):
        db = AsyncMock()
        db.add = MagicMock()
        svc = business_roadmap.BusinessRoadmapService(db)
        
        biz_id = uuid.uuid4()
        roadmap_id = uuid.uuid4()
        
        # Test init default
        db.execute.return_value = MagicMock(scalar_one_or_none=lambda: None)
        await svc.init_default_roadmap(biz_id)
        db.add.assert_called()
        
        # Test recalculation logic
        stage1 = models.RoadmapStage(status=RoadmapStageStatus.COMPLETED)
        stage2 = models.RoadmapStage(status=RoadmapStageStatus.PLANNED)
        
        mock_stages = MagicMock()
        mock_stages.scalars().all.return_value = [stage1, stage2]
        db.execute.return_value = mock_stages
        
        mock_roadmap = models.BusinessRoadmap(id=roadmap_id)
        db.get.return_value = mock_roadmap
        db.execute.side_effect = [mock_stages, MagicMock(scalar_one_or_none=lambda: mock_roadmap)]
        
        await svc._recalculate_roadmap_completion(roadmap_id)
        assert mock_roadmap.completion_percentage == 50.0
        
        # Test transition stage
        stage_obj = models.RoadmapStage(id=uuid.uuid4(), roadmap_id=roadmap_id, order_index=0)
        db.execute.side_effect = None
        db.execute.return_value = MagicMock(scalar_one_or_none=lambda: stage_obj)
        await svc.transition_stage(stage_obj.id, RoadmapStageStatus.COMPLETED)
        assert stage_obj.status == RoadmapStageStatus.COMPLETED
        
        # Test transition with prerequisite failure
        stage_obj_2 = models.RoadmapStage(id=uuid.uuid4(), roadmap_id=roadmap_id, order_index=1)
        db.execute.side_effect = [
            MagicMock(scalar_one_or_none=lambda: stage_obj_2), # get_roadmap_stage
            MagicMock(scalar_one_or_none=lambda: stage2)      # prev_stage (not completed)
        ]
        with pytest.raises(ValueError, match="Prerequisite stage not completed"):
            await svc.transition_stage(stage_obj_2.id, RoadmapStageStatus.ACTIVE)

    async def test_business_collaborator_management(self):
        db = AsyncMock()
        db.add = MagicMock()
        svc = business_collaborator.BusinessCollaboratorService(db)
        
        biz_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        # Test add collaborator (new)
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_res
        
        await svc.add_collaborator(biz_id, user_id, CollaboratorRole.EDITOR)
        db.add.assert_called()
        
        # Test remove collaborator
        collab = models.BusinessCollaborator(role=CollaboratorRole.EDITOR)
        db.execute.return_value.scalar_one_or_none.return_value = collab
        await svc.remove_collaborator(biz_id, user_id)
        db.delete.assert_called_once()
        
        # Test remove owner (forbidden)
        collab.role = CollaboratorRole.OWNER
        db.execute.return_value.scalar_one_or_none.return_value = collab # For delete_business_collaborator lookup
        with pytest.raises(PermissionError):
            await svc.delete_business_collaborator(uuid.uuid4())
        
        # Handler test
        with patch("app.db.database.AsyncSessionLocal") as mock_session:
            mock_session.return_value.__aenter__.return_value = db
            biz = MagicMock(id=biz_id, owner_id=user_id)
            await business_collaborator.BusinessCollaboratorService.handle_business_event("created", {"business": biz})
            db.add.assert_called()

    async def test_business_invites(self):
        db = AsyncMock()
        db.add = MagicMock()
        
        biz_id = uuid.uuid4()
        email = "test@invite.com"
        token = "secret"
        
        # Test create
        svc = business_invite.BusinessInviteService(db)
        invite = await svc.create_invite(biz_id, email, uuid.uuid4())
        assert invite.email == email
        db.add.assert_called()
        
        # Test accept_invite (success)
        user_id = uuid.uuid4()
        invite_obj = models.BusinessInvite(
            business_id=biz_id, 
            email=email, 
            token=token, 
            status=InviteStatus.PENDING,
            expires_at=datetime.now(timezone.utc) + timedelta(days=1)
        )
        db.execute.return_value = MagicMock(scalar_one_or_none=lambda: invite_obj)
        
        svc = business_invite.BusinessInviteService(db)
        success = await svc.accept_invite(token, user_id)
        assert success is True
        assert invite_obj.status == InviteStatus.ACCEPTED
        
        # Test accept_invite (expired)
        invite_obj.status = InviteStatus.PENDING
        invite_obj.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        success = await business_invite.accept_invite(db, token, user_id)
        assert success is False
        assert invite_obj.status == InviteStatus.EXPIRED
        
        # Test update_invite with acceptance trigger
        invite_obj.status = InviteStatus.PENDING # Reset
        # update_business_invite calls db.execute(select(User))
        # Then calls collab_service.add_collaborator which calls db.execute(select(BusinessCollaborator))
        mock_user_res = MagicMock(scalar_one_or_none=lambda: models.User(id=user_id))
        mock_collab_res = MagicMock(scalar_one_or_none=lambda: None) # No existing collab
        db.execute.side_effect = [mock_user_res, mock_collab_res]
        
        await business_invite.update_business_invite(db, invite_obj, {"status": InviteStatus.ACCEPTED})
        assert invite_obj.status == InviteStatus.ACCEPTED
        db.add.assert_called()


