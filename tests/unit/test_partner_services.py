import pytest
from sqlalchemy.orm import Session
from app.models.enums import PartnerType, ApprovalStatus, RequestStatus, BusinessStage
from app.models.business.business import Business
from app.services.partners.partner_profile_service import approve_partner_profile, create_partner_profile
from app.services.partners.partner_request_service import accept_partner_request, create_partner_request
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
    profile = create_partner_profile(db, obj_in)
    return profile

def test_partner_profile_approval(db: Session, test_partner_profile, test_user):
    # 1. Initially PENDING
    assert test_partner_profile.approval_status == ApprovalStatus.PENDING
    
    # 2. Approve
    approved = approve_partner_profile(db, test_partner_profile.id, test_user.id)
    assert approved.approval_status == ApprovalStatus.APPROVED
    assert approved.approved_by == test_user.id

def test_partner_request_flow(db: Session, test_business, test_partner_profile, test_user):
    # 1. Create Request
    obj_in = PartnerRequestCreate(
        business_id=test_business.id,
        partner_id=test_partner_profile.id,
        requested_by=test_user.id
    )
    req = create_partner_request(db, obj_in)
    assert req.status == RequestStatus.PENDING
    
    # 2. Accept Request
    accepted = accept_partner_request(db, req.id)
    assert accepted.status == RequestStatus.ACCEPTED
