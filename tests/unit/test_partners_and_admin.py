"""Tests covering PartnerRequest, PartnerProfile and AdminLogService unique branches."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import uuid

from app.models.enums import ApprovalStatus, RequestStatus
from app.services.partners.partner_profile import PartnerProfileService, get_partner_profile_service
from app.services.partners.partner_request import PartnerRequestService, get_partner_request_service
from app.services.partners.partner_service import get_detailed_status, reset_internal_state
from app.services.users.admin_log_service import AdminLogService, get_admin_log_service


# ── AdminLogService ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_log_service_exhaustive():
    db = AsyncMock()
    svc = AdminLogService(db)
    svc.repo = AsyncMock()
    uid = uuid.uuid4()

    await svc.get_admin_action_log(uid)
    await svc.get_admin_action_logs()
    
    await svc.get_admin_logs(0, 50)
    
    await svc.create_admin_action_log({"action": "A"}, auto_commit=False)
    svc.repo.create.assert_called()
    
    await svc.update_admin_action_log(MagicMock(), {"action": "B"})
    
    svc.repo.get.return_value = None
    assert await svc.delete_admin_action_log(uid) is None
    
    db_obj = MagicMock()
    svc.repo.get.return_value = db_obj
    await svc.delete_admin_action_log(uid)
    svc.repo.delete.assert_called_with(db_obj)

    await get_admin_log_service(db)


# ── PartnerProfileService ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_partner_profile_service_exhaustive():
    db = AsyncMock()
    svc = PartnerProfileService(db)
    svc.repo = AsyncMock()
    uid = uuid.uuid4()

    await svc.get_partner_profile(uid)
    await svc.get_partner_profiles()
    
    # create: obj_in dict
    await svc.create_partner_profile(obj_in={"bio": "text", "details": {"a": "b"}})
    
    # create: user_id is an object
    class DummyUser:
        def model_dump(self, **kwargs):
            return {"user_id": uid, "bio": "abc"}
    await svc.create_partner_profile(user_id=DummyUser())
    
    # create: explicit fields
    await svc.create_partner_profile(user_id=uid, bio="abc", details={"b": "a"})

    # update & delete
    await svc.update_partner_profile(MagicMock(), {"bio": "123"})
    await svc.delete_partner_profile(uid)

    # approve
    svc.repo.get.return_value = None
    assert await svc.approve_partner_profile(uid, uid) is None
    
    svc.repo.get.return_value = MagicMock()
    await svc.approve_partner_profile(uid, uid)

    # match_partners_by_capability
    svc.repo.get_approved_by_type.return_value = []
    await svc.match_partners_by_capability({"required_type": "AGENCY"})
    
    mock_partner_1 = MagicMock(
        services_json={"skills": ["Python"], "industry": "Tech", "min_budget": 50, "max_budget": 100},
        experience_json={"skills": ["Go"]}
    )
    mock_partner_2 = MagicMock(
        services_json={"skills": ["Java"]},
        experience_json={"skills": ["Python"], "industry": "Tech"}
    )
    mock_partner_3 = MagicMock(
        services_json={"min_budget": 200, "max_budget": 500},
        experience_json=None
    )
    
    svc.repo.get_approved_by_type.return_value = [mock_partner_1, mock_partner_2, mock_partner_3]
    
    # Matching budget, industry, and skills
    res = await svc.match_partners_by_capability({
        "required_type": "AGENCY",
        "skills": ["Python", "Rust"],
        "industry": "Tech",
        "budget": 75
    })
    
    assert len(res) == 3
    
    await get_partner_profile_service(db)


# ── PartnerRequestService ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_partner_request_service_exhaustive():
    db = AsyncMock()
    svc = PartnerRequestService(db)
    svc.repo = AsyncMock()
    uid = uuid.uuid4()
    
    await svc.get_partner_request(uid)
    await svc.get_partner_requests()
    
    # submit_partner_request
    # context is string (valid JSON)
    await svc.submit_partner_request(uid, uid, context='{"a": "b"}')
    # context is string (invalid JSON)
    await svc.submit_partner_request(uid, uid, context='invalid json')
    # context is dict
    await svc.submit_partner_request(uid, uid, context={"a": "b"})
    
    await svc.create_partner_request({"business_id": uid})
    await svc.update_partner_request(MagicMock(), {"business_id": uid})
    await svc.delete_partner_request(uid)
    
    # transition & accept
    svc.repo.get.return_value = None
    assert await svc.transition_request_status(uid, RequestStatus.ACCEPTED) is None
    
    svc.repo.get.return_value = MagicMock()
    await svc.accept_partner_request(uid)

    await get_partner_request_service(db)

# ── partner_service.py Legacy Alias and Status ─────────────────────────────────

def test_partner_service_utils():
    status = get_detailed_status()
    assert status["module"] == "partner_service"
    reset_internal_state() # Just hits logger
