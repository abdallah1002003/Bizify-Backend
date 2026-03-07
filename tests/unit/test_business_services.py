"""Tests for BusinessService, BusinessRoadmapService, and BusinessInviteServiceFacade."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import uuid

from app.models.enums import RoadmapStageStatus, StageType
from app.services.business.business_roadmap import (
    BusinessRoadmapService, get_business_roadmap_service, register_business_roadmap_handlers
)
from app.services.business.business_service import (
    BusinessService, get_business_service
)
from app.services.business.business_invite_service import (
    BusinessInviteServiceFacade
)


# ── BusinessService ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_business_service_exhaustive():
    db = AsyncMock()
    mock_roadmap = AsyncMock()
    mock_collaborator = AsyncMock()
    
    svc = BusinessService(db, roadmap_service=mock_roadmap, collaborator_service=mock_collaborator)
    svc.repo = AsyncMock()
    uid = uuid.uuid4()
    owner_id = uuid.uuid4()

    # get_business
    await svc.get_business(uid)
    svc.repo.get_with_relations.assert_called_with(uid)

    # get_businesses
    await svc.get_businesses(owner_id=owner_id)
    svc.repo.get_all_filtered.assert_called_with(owner_id=owner_id, skip=0, limit=100)

    # create_business
    db_obj = MagicMock(id=uid)
    svc.repo.create.return_value = db_obj
    result = await svc.create_business({"name": "Test Business"})
    assert result == db_obj
    mock_roadmap.init_default_roadmap.assert_called_with(uid)

    # update_business
    await svc.update_business(db_obj, {"name": "New Name"})
    svc.repo.update.assert_called()

    # delete_business
    await svc.delete_business(uid)
    svc.repo.delete.assert_called_with(uid)

    # update_business_stage: not found
    svc.repo.get_with_relations.return_value = None
    assert await svc.update_business_stage(uid, "STAGE2") is None

    # update_business_stage: found
    svc.repo.get_with_relations.return_value = db_obj
    await svc.update_business_stage(uid, "STAGE2")
    svc.repo.update.assert_called_with(db_obj, {"stage": "STAGE2"})

    # get_business_service (factory)
    await get_business_service(db)
    await get_business_service(db, roadmap=mock_roadmap, collaborator=mock_collaborator)


# ── BusinessRoadmapService ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_business_roadmap_service_exhaustive():
    db = AsyncMock()
    svc = BusinessRoadmapService(db)
    svc.roadmap_repo = AsyncMock()
    svc.stage_repo = AsyncMock()
    uid = uuid.uuid4()
    business_id = uuid.uuid4()

    # _recalculate_roadmap_completion: no stages
    svc.stage_repo.get_all_for_roadmap_unordered.return_value = []
    await svc._recalculate_roadmap_completion(uid)

    # _recalculate_roadmap_completion: roadmap not found
    stage_mock = MagicMock(status=RoadmapStageStatus.COMPLETED)
    svc.stage_repo.get_all_for_roadmap_unordered.return_value = [stage_mock]
    svc.roadmap_repo.get.return_value = None
    await svc._recalculate_roadmap_completion(uid)

    # _recalculate_roadmap_completion: valid recalculation
    svc.roadmap_repo.get.return_value = MagicMock()
    await svc._recalculate_roadmap_completion(uid)
    svc.roadmap_repo.update.assert_called()

    # get_roadmap, get_business_roadmap, get_business_roadmaps
    await svc.get_roadmap(business_id)
    await svc.get_business_roadmap(uid)
    await svc.get_business_roadmaps()

    # init_default_roadmap: already exists
    svc.roadmap_repo.get_by_business.return_value = MagicMock()
    await svc.init_default_roadmap(business_id)

    # init_default_roadmap: new
    svc.roadmap_repo.get_by_business.return_value = None
    new_roadmap = MagicMock(id=uuid.uuid4())
    svc.roadmap_repo.create.return_value = new_roadmap
    await svc.init_default_roadmap(business_id)
    svc.stage_repo.create.assert_called()

    # create / update / delete
    await svc.create_business_roadmap({"business_id": business_id})
    await svc.update_business_roadmap(MagicMock(), {"completion_percentage": 10})
    
    svc.roadmap_repo.get.return_value = MagicMock()
    await svc.delete_business_roadmap(uid)
    
    svc.roadmap_repo.get.return_value = None
    assert await svc.delete_business_roadmap(uid) is None

    # get_roadmap_stage
    await svc.get_roadmap_stage(uid)

    # get_roadmap_stages
    await svc.get_roadmap_stages()
    await svc.get_roadmap_stages(roadmap_id=uid)

    # add_roadmap_stage
    await svc.add_roadmap_stage(uid, StageType.READINESS, 1)

    # create_roadmap_stage
    await svc.create_roadmap_stage({"roadmap_id": uid})

    # update_roadmap_stage: not completed
    db_stage = MagicMock()
    updated_stage_not_completed = MagicMock(status=RoadmapStageStatus.PLANNED)
    svc.stage_repo.update.return_value = updated_stage_not_completed
    await svc.update_roadmap_stage(db_stage, {"status": "PLANNED"})

    # update_roadmap_stage: completed (triggers recalculate)
    updated_stage_completed = MagicMock(status=RoadmapStageStatus.COMPLETED, roadmap_id=uid)
    svc.stage_repo.update.return_value = updated_stage_completed
    with patch.object(svc, "_recalculate_roadmap_completion", new_callable=AsyncMock) as m_recalc:
        await svc.update_roadmap_stage(db_stage, {"status": "COMPLETED"})
        m_recalc.assert_called_with(uid)

    # delete_roadmap_stage: found
    svc.stage_repo.get.return_value = MagicMock(roadmap_id=uid)
    with patch.object(svc, "_recalculate_roadmap_completion", new_callable=AsyncMock) as m_recalc:
        await svc.delete_roadmap_stage(uid)
        m_recalc.assert_called_with(uid)
        
    # delete_roadmap_stage: not found
    svc.stage_repo.get.return_value = None
    assert await svc.delete_roadmap_stage(uid) is None

    # transition_stage: not found
    svc.stage_repo.get_with_relations.return_value = None
    assert await svc.transition_stage(uid, RoadmapStageStatus.ACTIVE) is None

    # transition_stage: ACTIVE with prior stage not completed
    db_stage = MagicMock(order_index=1, roadmap_id=uid)
    svc.stage_repo.get_with_relations.return_value = db_stage
    svc.stage_repo.get_by_order_index.return_value = MagicMock(status=RoadmapStageStatus.PLANNED)
    with pytest.raises(ValueError, match="Prerequisite stage not completed"):
        await svc.transition_stage(uid, RoadmapStageStatus.ACTIVE)

    # transition_stage: prior stage completed or order_index 0, new_status = COMPLETED
    db_stage.order_index = 0
    svc.stage_repo.update.return_value = MagicMock(roadmap_id=uid)
    with patch.object(svc, "_recalculate_roadmap_completion", new_callable=AsyncMock) as m_recalc:
        await svc.transition_stage(uid, RoadmapStageStatus.COMPLETED)
        m_recalc.assert_called_with(uid)

    # register_business_roadmap_handlers
    register_business_roadmap_handlers()

    # handle_business_event: no business
    await BusinessRoadmapService.handle_business_event("business.created", {})

    # handle_business_event: setup success
    with patch("app.db.database.AsyncSessionLocal") as m_session:
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=AsyncMock())
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        m_session.return_value = mock_ctx

        with patch.object(BusinessRoadmapService, "init_default_roadmap", new_callable=AsyncMock):
            await BusinessRoadmapService.handle_business_event(
                "business.created", {"business": MagicMock(id=business_id)}
            )

    # handle_business_event: setup failure
    with patch("app.db.database.AsyncSessionLocal") as m_session2:
        mock_ctx2 = AsyncMock()
        mock_ctx2.__aenter__ = AsyncMock(return_value=AsyncMock())
        mock_ctx2.__aexit__ = AsyncMock(return_value=False)
        m_session2.return_value = mock_ctx2

        with patch.object(BusinessRoadmapService, "init_default_roadmap", 
                          new_callable=AsyncMock, side_effect=Exception("DB fail")):
            await BusinessRoadmapService.handle_business_event(
                "business.created", {"business": MagicMock(id=business_id)}
            )

    # Dependency provider
    await get_business_roadmap_service(db)


# ── BusinessInviteServiceFacade ────────────────────────────────────────────────

def test_business_invite_service_facade():
    """Test standard facade inheritance parsing."""
    facade = BusinessInviteServiceFacade(AsyncMock())
    assert isinstance(facade, BusinessInviteServiceFacade)
