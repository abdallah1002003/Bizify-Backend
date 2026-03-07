# ruff: noqa
import pytest
import pytest_asyncio
from app.models.enums import PartnerType, ApprovalStatus, RequestStatus, BusinessStage
from app.models.business.business import Business
from app.services.partners import partner_service
<<<<<<< HEAD
from app.services.partners.partner_profile import PartnerProfileService
from app.services.partners.partner_request import PartnerRequestService
=======
>>>>>>> origin/main
from app.schemas.partners.partner_profile import PartnerProfileCreate
from app.schemas.partners.partner_request import PartnerRequestCreate

@pytest_asyncio.fixture
async def test_business(async_db, test_user):
    biz = Business(owner_id=test_user.id, stage=BusinessStage.EARLY)
    async_db.add(biz)
    await async_db.commit()
    await async_db.refresh(biz)
    return biz

@pytest_asyncio.fixture
async def test_partner_profile(async_db, test_user):
    obj_in = PartnerProfileCreate(
        user_id=test_user.id,
        partner_type=PartnerType.MENTOR,
        company_name="Advisor Co"
    )
<<<<<<< HEAD
    profile = await PartnerProfileService(async_db).create_partner_profile(obj_in=obj_in)
=======
    profile = await partner_service.create_partner_profile(async_db, obj_in=obj_in)
>>>>>>> origin/main
    return profile

@pytest.mark.asyncio
async def test_partner_profile_approval(async_db, test_partner_profile, test_user):
    assert test_partner_profile.approval_status == ApprovalStatus.PENDING
<<<<<<< HEAD
    approved = await PartnerProfileService(async_db).approve_partner_profile(test_partner_profile.id, test_user.id)
=======
    approved = await partner_service.approve_partner_profile(async_db, test_partner_profile.id, test_user.id)
>>>>>>> origin/main
    assert approved.approval_status == ApprovalStatus.APPROVED
    assert approved.approved_by == test_user.id

@pytest.mark.asyncio
async def test_partner_request_flow(async_db, test_business, test_partner_profile, test_user):
    obj_in = PartnerRequestCreate(
        business_id=test_business.id,
        partner_id=test_partner_profile.id,
        requested_by=test_user.id
    )
<<<<<<< HEAD
    req = await PartnerRequestService(async_db).create_partner_request(obj_in)
    assert req.status == RequestStatus.PENDING
    accepted = await PartnerRequestService(async_db).accept_partner_request(req.id)
=======
    req = await partner_service.create_partner_request(async_db, obj_in)
    assert req.status == RequestStatus.PENDING
    accepted = await partner_service.accept_partner_request(async_db, req.id)
>>>>>>> origin/main
    assert accepted.status == RequestStatus.ACCEPTED

@pytest.mark.asyncio
async def test_get_multiple_partner_profiles(async_db, test_user, test_partner_profile):
<<<<<<< HEAD
    profiles = await PartnerProfileService(async_db).get_partner_profiles(skip=0, limit=10)
=======
    profiles = await partner_service.get_partner_profiles(async_db, skip=0, limit=10)
>>>>>>> origin/main
    assert len(profiles) >= 1

@pytest.mark.asyncio
async def test_create_partner_profile_raw_args(async_db, test_user):
<<<<<<< HEAD
    profile = await PartnerProfileService(async_db).create_partner_profile(obj_in={
        "user_id": test_user.id,
        "partner_type": PartnerType.MANUFACTURER,
        "bio": "Test Bio",
        "details": {"key": "value"}
    })
=======
    profile = await partner_service.create_partner_profile(
        async_db,
        user_id=test_user.id,
        partner_type=PartnerType.MANUFACTURER,
        bio="Test Bio",
        details={"key": "value"}
    )
>>>>>>> origin/main
    assert profile.partner_type == PartnerType.MANUFACTURER
    assert profile.description == "Test Bio"
    assert profile.approval_status == ApprovalStatus.PENDING

@pytest.mark.asyncio
async def test_update_and_delete_partner_profile(async_db, test_partner_profile):
    obj_in_update = {"partner_type": PartnerType.SUPPLIER}
<<<<<<< HEAD
    updated = await PartnerProfileService(async_db).update_partner_profile(test_partner_profile, obj_in_update)
    assert updated.partner_type == PartnerType.SUPPLIER
    deleted = await PartnerProfileService(async_db).delete_partner_profile(test_partner_profile.id)
    assert deleted is not None
    assert await PartnerProfileService(async_db).get_partner_profile(test_partner_profile.id) is None
=======
    updated = await partner_service.update_partner_profile(async_db, test_partner_profile, obj_in_update)
    assert updated.partner_type == PartnerType.SUPPLIER
    deleted = await partner_service.delete_partner_profile(async_db, test_partner_profile.id)
    assert deleted is not None
    assert await partner_service.get_partner_profile(async_db, test_partner_profile.id) is None
>>>>>>> origin/main

@pytest.mark.asyncio
async def test_delete_nonexistent_partner_profile(async_db):
    import uuid
<<<<<<< HEAD
    assert await PartnerProfileService(async_db).delete_partner_profile(uuid.uuid4()) is None
=======
    assert await partner_service.delete_partner_profile(async_db, uuid.uuid4()) is None
>>>>>>> origin/main

@pytest.mark.asyncio
async def test_approve_nonexistent_partner_profile(async_db, test_user):
    import uuid
<<<<<<< HEAD
    assert await PartnerProfileService(async_db).approve_partner_profile(uuid.uuid4(), test_user.id) is None

@pytest.mark.asyncio
async def test_match_partners_by_capability_scoring(async_db, test_user):
    p1 = await PartnerProfileService(async_db).create_partner_profile(obj_in=
        {"user_id": test_user.id, 
        "partner_type": PartnerType.MENTOR,
        "details": {"skills": ["python", "fastapi"], "industry": "Tech", "min_budget": 1000, "max_budget": 5000}}
    )
    await PartnerProfileService(async_db).approve_partner_profile(p1.id, test_user.id)
    p2 = await PartnerProfileService(async_db).create_partner_profile(obj_in=
        {"user_id": test_user.id, 
        "partner_type": PartnerType.MENTOR,
        "details": {"skills": ["python"], "industry": "Finance", "min_budget": 5000}}
    )
    await PartnerProfileService(async_db).approve_partner_profile(p2.id, test_user.id)
    p3 = await PartnerProfileService(async_db).create_partner_profile(obj_in=
        {"user_id": test_user.id, 
        "partner_type": PartnerType.SUPPLIER,
        "details": {"skills": ["python", "fastapi"], "industry": "Tech"}}
    )
    await PartnerProfileService(async_db).approve_partner_profile(p3.id, test_user.id)
    p4 = await PartnerProfileService(async_db).create_partner_profile(obj_in=
        {"user_id": test_user.id, 
        "partner_type": PartnerType.MENTOR,
        "details": {"skills": ["python", "fastapi"], "industry": "Tech"}}
=======
    assert await partner_service.approve_partner_profile(async_db, uuid.uuid4(), test_user.id) is None

@pytest.mark.asyncio
async def test_match_partners_by_capability_scoring(async_db, test_user):
    p1 = await partner_service.create_partner_profile(
        async_db, 
        user_id=test_user.id, 
        partner_type=PartnerType.MENTOR,
        details={"skills": ["python", "fastapi"], "industry": "Tech", "min_budget": 1000, "max_budget": 5000}
    )
    await partner_service.approve_partner_profile(async_db, p1.id, test_user.id)
    p2 = await partner_service.create_partner_profile(
        async_db, 
        user_id=test_user.id, 
        partner_type=PartnerType.MENTOR,
        details={"skills": ["python"], "industry": "Finance", "min_budget": 5000}
    )
    await partner_service.approve_partner_profile(async_db, p2.id, test_user.id)
    p3 = await partner_service.create_partner_profile(
        async_db, 
        user_id=test_user.id, 
        partner_type=PartnerType.SUPPLIER,
        details={"skills": ["python", "fastapi"], "industry": "Tech"}
    )
    await partner_service.approve_partner_profile(async_db, p3.id, test_user.id)
    p4 = await partner_service.create_partner_profile(
        async_db, 
        user_id=test_user.id, 
        partner_type=PartnerType.MENTOR,
        details={"skills": ["python", "fastapi"], "industry": "Tech"}
>>>>>>> origin/main
    )
    needs_1 = {
        "required_type": PartnerType.MENTOR,
        "skills": ["python", "fastapi"],
        "industry": "Tech",
        "budget": 3000
    }
<<<<<<< HEAD
    matches = await PartnerProfileService(async_db).match_partners_by_capability(needs_1)
=======
    matches = await partner_service.match_partners_by_capability(async_db, needs_1)
>>>>>>> origin/main
    assert len(matches) == 2
    assert matches[0].id == p1.id
    assert matches[1].id == p2.id
    needs_2 = {
        "industry": "Finance",
        "skills": ["python"] 
    }
<<<<<<< HEAD
    matches2 = await PartnerProfileService(async_db).match_partners_by_capability(needs_2)
=======
    matches2 = await partner_service.match_partners_by_capability(async_db, needs_2)
>>>>>>> origin/main
    assert len(matches2) == 3
    assert matches2[0].id == p2.id

@pytest.mark.asyncio
async def test_get_multiple_partner_requests(async_db, test_business, test_partner_profile, test_user):
<<<<<<< HEAD
    await PartnerRequestService(async_db).submit_partner_request(test_business.id, test_partner_profile.id, requested_by=test_user.id)
    requests = await PartnerRequestService(async_db).get_partner_requests(skip=0, limit=10)
=======
    await partner_service.submit_partner_request(async_db, test_business.id, test_partner_profile.id, requested_by=test_user.id)
    requests = await partner_service.get_partner_requests(async_db, skip=0, limit=10)
>>>>>>> origin/main
    assert len(requests) >= 1

@pytest.mark.asyncio
async def test_update_and_delete_partner_request(async_db, test_business, test_partner_profile, test_user):
<<<<<<< HEAD
    req = await PartnerRequestService(async_db).submit_partner_request(test_business.id, test_partner_profile.id, requested_by=test_user.id)
    updated = await PartnerRequestService(async_db).update_partner_request(req, {"status": RequestStatus.REJECTED})
    assert updated.status == RequestStatus.REJECTED
    deleted = await PartnerRequestService(async_db).delete_partner_request(req.id)
    assert deleted is not None
    assert await PartnerRequestService(async_db).get_partner_request(req.id) is None
=======
    req = await partner_service.submit_partner_request(async_db, test_business.id, test_partner_profile.id, requested_by=test_user.id)
    updated = await partner_service.update_partner_request(async_db, req, {"status": RequestStatus.REJECTED})
    assert updated.status == RequestStatus.REJECTED
    deleted = await partner_service.delete_partner_request(async_db, req.id)
    assert deleted is not None
    assert await partner_service.get_partner_request(async_db, req.id) is None
>>>>>>> origin/main

@pytest.mark.asyncio
async def test_delete_nonexistent_partner_request(async_db):
    import uuid
<<<<<<< HEAD
    assert await PartnerRequestService(async_db).delete_partner_request(uuid.uuid4()) is None
=======
    assert await partner_service.delete_partner_request(async_db, uuid.uuid4()) is None
>>>>>>> origin/main

@pytest.mark.asyncio
async def test_transition_request_status_nonexistent(async_db):
    import uuid
<<<<<<< HEAD
    assert await PartnerRequestService(async_db).transition_request_status(uuid.uuid4(), RequestStatus.ACCEPTED) is None
=======
    assert await partner_service.transition_request_status(async_db, uuid.uuid4(), RequestStatus.ACCEPTED) is None
>>>>>>> origin/main

@pytest.mark.asyncio
async def test_partner_service_utils():
    status = partner_service.get_detailed_status()
    assert status["module"] == "partner_service"
    assert status["status"] == "operational"
    partner_service.reset_internal_state()

@pytest.mark.asyncio
async def test_max_budget_exclusion(async_db, test_user):
<<<<<<< HEAD
    p5 = await PartnerProfileService(async_db).create_partner_profile(obj_in=
        {"user_id": test_user.id, 
        "partner_type": PartnerType.MENTOR,
        "details": {"skills": ["python", "fastapi"], "industry": "Tech", "max_budget": 500}}
    )
    await PartnerProfileService(async_db).approve_partner_profile(p5.id, test_user.id)
    needs_3 = {
        "budget": 800
    }
    matches3 = await PartnerProfileService(async_db).match_partners_by_capability(needs_3)
=======
    p5 = await partner_service.create_partner_profile(
        async_db, 
        user_id=test_user.id, 
        partner_type=PartnerType.MENTOR,
        details={"skills": ["python", "fastapi"], "industry": "Tech", "max_budget": 500}
    )
    await partner_service.approve_partner_profile(async_db, p5.id, test_user.id)
    needs_3 = {
        "budget": 800
    }
    matches3 = await partner_service.match_partners_by_capability(async_db, needs_3)
>>>>>>> origin/main
    assert len(matches3) == 1

@pytest.mark.asyncio
async def test_partner_model_dump_initialization(async_db, test_user):
    schema_payload = PartnerProfileCreate(
        user_id=test_user.id,
        partner_type=PartnerType.SUPPLIER,
        company_name="Dump Co"
    )
<<<<<<< HEAD
    profile = await PartnerProfileService(async_db).create_partner_profile(obj_in=schema_payload)
=======
    profile = await partner_service.create_partner_profile(async_db, user_id=schema_payload)
>>>>>>> origin/main
    assert profile.partner_type == PartnerType.SUPPLIER

