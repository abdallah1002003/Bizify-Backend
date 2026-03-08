"""Tests covering AgentService and AgentRunService missing branches."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import uuid

from app.services.ai.agent_service import AgentService, get_agent_service
from app.services.ai.agent_run_service import AgentRunService, get_agent_run_service

# ── AgentService ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_agent_service_exhaustive():
    db = AsyncMock()
    svc = AgentService(db)
    svc.repo = AsyncMock()
    uid = uuid.uuid4()

    await svc.get_agent(uid)
    await svc.get_agents()
    
    await svc.create_agent("N", "P", {"c": 1})
    svc.repo.create.assert_called()
    
    await svc.update_agent(MagicMock(), {"name": "N2"})
    
    svc.repo.get.return_value = None
    assert await svc.delete_agent(uid) is None
    
    db_obj = MagicMock()
    svc.repo.get.return_value = db_obj
    await svc.delete_agent(uid)
    svc.repo.delete.assert_called_with(db_obj)

    await get_agent_service(db)

# ── AgentRunService ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_agent_run_service_exhaustive():
    db = AsyncMock()
    billing = AsyncMock()
    svc = AgentRunService(db, billing)
    svc.repo = AsyncMock()
    svc.validation_repo = AsyncMock()
    uid = uuid.uuid4()

    await svc.get_agent_run(uid)
    await svc.get_agent_runs()
    await svc.get_agent_runs(user_id=uid)
    
    # initiate_agent_run without user
    await svc.initiate_agent_run(uid, None, uid, {"a": "b"})
    
    # initiate_agent_run with user (billing false)
    billing.check_usage_limit.return_value = False
    with pytest.raises(PermissionError, match="Insufficient AI quota"):
        await svc.initiate_agent_run(uid, uid, uid, {"a": "b"})
        
    # initiate_agent_run with user (billing true)
    billing.check_usage_limit.return_value = True
    await svc.initiate_agent_run(uid, uid, uid, {"a": "b"})
    billing.record_usage.assert_called()

    # execute_agent_run_async
    with patch.object(svc, "get_agent_run", return_value=None):
        assert await svc.execute_agent_run_async(uid) is None
        
    # valid execution
    db_obj = MagicMock()
    db_obj.stage.stage_type.value = "test_stage"
    db_obj.agent.name = "TestAgent"
    db_obj.input_data = {"k": "v"}
    svc.repo.update.return_value = db_obj
    
    with patch("app.services.ai.agent_run_service.provider_runtime.AIProviderService") as mock_prov_class, \
         patch("app.services.ai.agent_run_service.dispatcher.emit", new_callable=AsyncMock) as mock_emit:
         
         mock_prov_inst = MagicMock()
         mock_prov_inst.run_agent_execution = AsyncMock(return_value={"score": 0.85, "summary": "done"})
         mock_prov_class.return_value = mock_prov_inst
         
         await svc.execute_agent_run_async(uid)
         mock_emit.assert_called_with("agent_run.completed", {"run_id": db_obj.id, "status": "SUCCESS"})
         svc.validation_repo.create.assert_called()
         
    # execution error
    with patch("app.services.ai.agent_run_service.provider_runtime.AIProviderService") as mock_prov_class, \
         patch("app.services.ai.agent_run_service.dispatcher.emit", new_callable=AsyncMock) as mock_emit:
         
         mock_prov_inst = MagicMock()
         mock_prov_inst.run_agent_execution = AsyncMock(side_effect=Exception("API Error"))
         mock_prov_class.return_value = mock_prov_inst
         
         await svc.execute_agent_run_async(uid)
         mock_emit.assert_called_with("agent_run.completed", {"run_id": db_obj.id, "status": "FAILED", "error": "API Error"})
         svc.validation_repo.create.assert_called()

    # remaining validation log methods
    await svc.get_validation_log(uid)
    await svc.record_validation_log(uid, "FAILED", "fail details")
    
    # get dependency
    await get_agent_run_service(db)
