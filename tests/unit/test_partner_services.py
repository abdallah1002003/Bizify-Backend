import pytest
from sqlalchemy.orm import Session
from app.models.enums import PartnerType, ApprovalStatus, RequestStatus, BusinessStage
from app.models.business.business import Business
from app.services.partners import partner_service
from app.schemas.partners.partner_profile import PartnerProfileCreate
from app.schemas.partners.partner_request import PartnerRequestCreate

@pytest.fixture
def test_business(db: Session, test_user):
    biz = Business(owner_id=test_user.id, stage=BusinessStage.EARLY)
    db.add(biz)
    db.commit()
    db.refresh(biz)
    return biz

@pytest.fixture
def test_partner_profile(db: Session, test_user):
    obj_in = PartnerProfileCreate(
        user_id=test_user.id,
        partner_type=PartnerType.MENTOR,
        company_name="Advisor Co"
    )
    profile = partner_service.create_partner_profile(db, obj_in=obj_in)
    return profile

def test_partner_profile_approval(db: Session, test_partner_profile, test_user):
    # 1. Initially PENDING
    assert test_partner_profile.approval_status == ApprovalStatus.PENDING
    
    # 2. Approve
    approved = partner_service.approve_partner_profile(db, test_partner_profile.id, test_user.id)
    assert approved.approval_status == ApprovalStatus.APPROVED
    assert approved.approved_by == test_user.id

def test_partner_request_flow(db: Session, test_business, test_partner_profile, test_user):
    # 1. Create Request
    obj_in = PartnerRequestCreate(
        business_id=test_business.id,
        partner_id=test_partner_profile.id,
        requested_by=test_user.id
    )
    req = partner_service.create_partner_request(db, obj_in)
    assert req.status == RequestStatus.PENDING
    
    # 2. Accept Request
    accepted = partner_service.accept_partner_request(db, req.id)
    assert accepted.status == RequestStatus.ACCEPTED


def test_get_multiple_partner_profiles(db: Session, test_user, test_partner_profile):
    profiles = partner_service.get_partner_profiles(db, skip=0, limit=10)
    assert len(profiles) >= 1

def test_create_partner_profile_raw_args(db: Session, test_user):
    profile = partner_service.create_partner_profile(
        db,
        user_id=test_user.id,
        partner_type=PartnerType.MANUFACTURER,
        bio="Test Bio",
        details={"key": "value"}
    )
    assert profile.partner_type == PartnerType.MANUFACTURER
    assert profile.description == "Test Bio"
    assert profile.approval_status == ApprovalStatus.PENDING

def test_update_and_delete_partner_profile(db: Session, test_partner_profile):
    obj_in_update = {"partner_type": PartnerType.SUPPLIER}
    updated = partner_service.update_partner_profile(db, test_partner_profile, obj_in_update)
    assert updated.partner_type == PartnerType.SUPPLIER
    
    deleted = partner_service.delete_partner_profile(db, test_partner_profile.id)
    assert deleted is not None
    assert partner_service.get_partner_profile(db, test_partner_profile.id) is None

def test_delete_nonexistent_partner_profile(db: Session):
    import uuid
    assert partner_service.delete_partner_profile(db, uuid.uuid4()) is None

def test_approve_nonexistent_partner_profile(db: Session, test_user):
    import uuid
    assert partner_service.approve_partner_profile(db, uuid.uuid4(), test_user.id) is None

def test_match_partners_by_capability_scoring(db: Session, test_user):
    # 1. Partner with exact industry and 2 skills
    p1 = partner_service.create_partner_profile(
        db, 
        user_id=test_user.id, 
        partner_type=PartnerType.MENTOR,
        details={"skills": ["python", "fastapi"], "industry": "Tech", "min_budget": 1000, "max_budget": 5000}
    )
    partner_service.approve_partner_profile(db, p1.id, test_user.id)
    
    # 2. Partner with different industry but 1 matching skill. Budget has strict min
    p2 = partner_service.create_partner_profile(
        db, 
        user_id=test_user.id, 
        partner_type=PartnerType.MENTOR,
        details={"skills": ["python"], "industry": "Finance", "min_budget": 5000}
    )
    partner_service.approve_partner_profile(db, p2.id, test_user.id)

    # 3. Partner with different type but similar skills
    p3 = partner_service.create_partner_profile(
        db, 
        user_id=test_user.id, 
        partner_type=PartnerType.SUPPLIER,
        details={"skills": ["python", "fastapi"], "industry": "Tech"}
    )
    partner_service.approve_partner_profile(db, p3.id, test_user.id)
    
    # 4. Unapproved partner (should not be returned at all)
    p4 = partner_service.create_partner_profile(
        db, 
        user_id=test_user.id, 
        partner_type=PartnerType.MENTOR,
        details={"skills": ["python", "fastapi"], "industry": "Tech"}
    )

    # Scenario 1: Exact fit for Tech, python/fastapi, budget 3000
    needs_1 = {
        "required_type": PartnerType.MENTOR,
        "skills": ["python", "fastapi"],
        "industry": "Tech",
        "budget": 3000
    }
    matches = partner_service.match_partners_by_capability(db, needs_1)
    
    assert len(matches) == 2
    assert matches[0].id == p1.id  # Highest score (skills + industry + budget match)
    assert matches[1].id == p2.id  # Lower score (only 1 skill, wrong industry, budget mismatch)
    
    # Scenario 2: Seeking Finance partner without budget constraint, regardless of type
    needs_2 = {
        "industry": "Finance",
        "skills": ["python"] 
    }
    matches2 = partner_service.match_partners_by_capability(db, needs_2)
    
    assert len(matches2) == 3
    assert matches2[0].id == p2.id # Highest score (industry match + 1 skill + default budget match = 5 + 2 + 3 = 10)

def test_get_multiple_partner_requests(db: Session, test_business, test_partner_profile, test_user):
    partner_service.submit_partner_request(db, test_business.id, test_partner_profile.id, requested_by=test_user.id)
    requests = partner_service.get_partner_requests(db, skip=0, limit=10)
    assert len(requests) >= 1

def test_update_and_delete_partner_request(db: Session, test_business, test_partner_profile, test_user):
    req = partner_service.submit_partner_request(db, test_business.id, test_partner_profile.id, requested_by=test_user.id)
    
    updated = partner_service.update_partner_request(db, req, {"status": RequestStatus.REJECTED})
    assert updated.status == RequestStatus.REJECTED
    
    deleted = partner_service.delete_partner_request(db, req.id)
    assert deleted is not None
    assert partner_service.get_partner_request(db, req.id) is None

def test_delete_nonexistent_partner_request(db: Session):
    import uuid
    assert partner_service.delete_partner_request(db, uuid.uuid4()) is None

def test_transition_request_status_nonexistent(db: Session):
    import uuid
    assert partner_service.transition_request_status(db, uuid.uuid4(), RequestStatus.ACCEPTED) is None

def test_partner_service_utils():
    status = partner_service.get_detailed_status()
    assert status["module"] == "partner_service"
    assert status["status"] == "operational"
    
    partner_service.reset_internal_state() # Just to cover the logger info

def test_max_budget_exclusion(db: Session, test_user):
    # Scenario 3: Seeking partner with max budget constraint
    p5 = partner_service.create_partner_profile(
        db, 
        user_id=test_user.id, 
        partner_type=PartnerType.MENTOR,
        details={"skills": ["python", "fastapi"], "industry": "Tech", "max_budget": 500}
    )
    partner_service.approve_partner_profile(db, p5.id, test_user.id)
    
    needs_3 = {
        "budget": 800  # P5 max_budget 500 (too big)
    }
    matches3 = partner_service.match_partners_by_capability(db, needs_3)
    # They should not receive the +3 budget bonus, hitting the `pass` logic
    assert len(matches3) == 1

def test_partner_model_dump_initialization(db: Session, test_user):
    # Test line 43 (`hasattr(user_id, "model_dump")`)
    schema_payload = PartnerProfileCreate(
        user_id=test_user.id,
        partner_type=PartnerType.SUPPLIER,
        company_name="Dump Co"
    )
    # Passed to user_id parameter as schema object
    profile = partner_service.create_partner_profile(db, user_id=schema_payload)
    assert profile.partner_type == PartnerType.SUPPLIER
