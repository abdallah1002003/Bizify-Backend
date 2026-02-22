"""
Comprehensive unit tests for partner services.

This module tests partner functionality including:
- Partner profile creation and management
- Partner request handling
- Approval workflow
- Query and filtering
"""

import pytest
from uuid import uuid4
from sqlalchemy.orm import Session

from app.models import User, PartnerProfile, PartnerRequest, Business
from app.models.enums import (
    UserRole, 
    PartnerType, 
    ApprovalStatus, 
    RequestStatus,
    BusinessStage,
)
from app.services.partners.partner_profile_service import (
    create_partner_profile,
    get_partner_profile,
    list_partner_profiles,
    update_partner_profile,
    delete_partner_profile,
    approve_partner_profile,
    reject_partner_profile,
)
from app.services.partners.partner_request_service import (
    create_partner_request,
    get_partner_request,
    accept_partner_request,
    reject_partner_request,
    list_partner_requests,
)
from app.schemas.partners.partner_profile import PartnerProfileCreate, PartnerProfileUpdate
from app.schemas.partners.partner_request import PartnerRequestCreate
from app.core.security import get_password_hash


@pytest.fixture
def test_user(db: Session):
    """Create a test user."""
    user = User(
        id=uuid4(),
        name="Partner Test User",
        email="partner@example.com",
        password_hash=get_password_hash("testpass123"),
        role=UserRole.ENTREPRENEUR,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_admin(db: Session):
    """Create a test admin for approvals."""
    admin = User(
        id=uuid4(),
        name="Admin User",
        email="admin@example.com",
        password_hash=get_password_hash("adminpass123"),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@pytest.fixture
def test_business(db: Session, test_user):
    """Create a test business."""
    business = Business(
        id=uuid4(),
        owner_id=test_user.id,
        name="Test Business",
        stage=BusinessStage.EARLY,
    )
    db.add(business)
    db.commit()
    db.refresh(business)
    return business


@pytest.fixture
def test_partner_profile(db: Session, test_user):
    """Create a test partner profile."""
    profile_data = PartnerProfileCreate(
        user_id=test_user.id,
        partner_type=PartnerType.MENTOR,
        company_name="Mentor Co",
        description="Experienced business mentor",
        expertise_areas=["AI", "Startups"],
    )
    return create_partner_profile(db, profile_data)


class TestPartnerProfileService:
    """Test partner profile management."""

    def test_create_partner_profile(self, db: Session, test_user):
        """Test creating a new partner profile."""
        profile_data = PartnerProfileCreate(
            user_id=test_user.id,
            partner_type=PartnerType.MENTOR,
            company_name="Mentor Co",
            description="Experienced mentor",
        )
        
        profile = create_partner_profile(db, profile_data)
        
        assert profile.user_id == test_user.id
        assert profile.partner_type == PartnerType.MENTOR
        assert profile.company_name == "Mentor Co"
        assert profile.approval_status == ApprovalStatus.PENDING

    def test_get_partner_profile(self, db: Session, test_partner_profile):
        """Test retrieving a partner profile."""
        retrieved = get_partner_profile(db, test_partner_profile.id)
        
        assert retrieved is not None
        assert retrieved.id == test_partner_profile.id
        assert retrieved.company_name == "Mentor Co"

    def test_list_partner_profiles(self, db: Session, test_user):
        """Test listing partner profiles."""
        for i in range(3):
            profile_data = PartnerProfileCreate(
                user_id=test_user.id,
                partner_type=PartnerType.MENTOR if i % 2 == 0 else PartnerType.INVESTOR,
                company_name=f"Company {i}",
            )
            create_partner_profile(db, profile_data)
        
        profiles = list_partner_profiles(db)
        
        assert len(profiles) >= 3

    def test_list_partner_profiles_filter_by_type(self, db: Session, test_user):
        """Test filtering partner profiles by type."""
        # Create mixed types
        for i in range(2):
            profile_data = PartnerProfileCreate(
                user_id=test_user.id,
                partner_type=PartnerType.MENTOR,
                company_name=f"Mentor {i}",
            )
            create_partner_profile(db, profile_data)
        
        for i in range(2):
            profile_data = PartnerProfileCreate(
                user_id=test_user.id,
                partner_type=PartnerType.INVESTOR,
                company_name=f"Investor {i}",
            )
            create_partner_profile(db, profile_data)
        
        mentor_profiles = list_partner_profiles(db, partner_type=PartnerType.MENTOR)
        
        assert all(p.partner_type == PartnerType.MENTOR for p in mentor_profiles)

    def test_list_partner_profiles_filter_by_status(self, db: Session, test_user, test_admin):
        """Test filtering partner profiles by approval status."""
        # Create and approve one
        profile_data = PartnerProfileCreate(
            user_id=test_user.id,
            partner_type=PartnerType.MENTOR,
            company_name="Approved Mentor",
        )
        approved = create_partner_profile(db, profile_data)
        approve_partner_profile(db, approved.id, test_admin.id)
        
        # Create another (pending)
        profile_data2 = PartnerProfileCreate(
            user_id=test_user.id,
            partner_type=PartnerType.INVESTOR,
            company_name="Pending Investor",
        )
        create_partner_profile(db, profile_data2)
        
        approved_profiles = list_partner_profiles(db, approval_status=ApprovalStatus.APPROVED)
        
        assert all(p.approval_status == ApprovalStatus.APPROVED for p in approved_profiles)

    def test_update_partner_profile(self, db: Session, test_partner_profile):
        """Test updating a partner profile."""
        update_data = PartnerProfileUpdate(
            company_name="Updated Mentor Co",
            description="More experienced mentor",
        )
        
        updated = update_partner_profile(db, test_partner_profile.id, update_data)
        
        assert updated.company_name == "Updated Mentor Co"
        assert updated.description == "More experienced mentor"

    def test_delete_partner_profile(self, db: Session, test_partner_profile):
        """Test deleting a partner profile."""
        profile_id = test_partner_profile.id
        
        delete_partner_profile(db, profile_id)
        
        retrieved = get_partner_profile(db, profile_id)
        assert retrieved is None

    def test_approve_partner_profile(self, db: Session, test_partner_profile, test_admin):
        """Test approving a partner profile."""
        assert test_partner_profile.approval_status == ApprovalStatus.PENDING
        assert test_partner_profile.approved_by is None
        
        approved = approve_partner_profile(db, test_partner_profile.id, test_admin.id)
        
        assert approved.approval_status == ApprovalStatus.APPROVED
        assert approved.approved_by == test_admin.id

    def test_reject_partner_profile(self, db: Session, test_partner_profile, test_admin):
        """Test rejecting a partner profile."""
        rejected = reject_partner_profile(
            db, 
            test_partner_profile.id, 
            test_admin.id,
            reason="Insufficient experience"
        )
        
        assert rejected.approval_status == ApprovalStatus.REJECTED
        assert rejected.approved_by == test_admin.id

    def test_cannot_approve_already_approved_profile(self, db: Session, test_partner_profile, test_admin):
        """Test that already approved profiles cannot be approved again."""
        approve_partner_profile(db, test_partner_profile.id, test_admin.id)
        
        with pytest.raises(ValueError, match="already approved"):
            approve_partner_profile(db, test_partner_profile.id, test_admin.id)


class TestPartnerRequestService:
    """Test partner request workflow."""

    def test_create_partner_request(self, db: Session, test_business, test_partner_profile, test_user):
        """Test creating a partner request."""
        request_data = PartnerRequestCreate(
            business_id=test_business.id,
            partner_id=test_partner_profile.id,
            requested_by=test_user.id,
        )
        
        request = create_partner_request(db, request_data)
        
        assert request.business_id == test_business.id
        assert request.partner_id == test_partner_profile.id
        assert request.status == RequestStatus.PENDING

    def test_get_partner_request(self, db: Session, test_business, test_partner_profile, test_user):
        """Test retrieving a partner request."""
        request_data = PartnerRequestCreate(
            business_id=test_business.id,
            partner_id=test_partner_profile.id,
            requested_by=test_user.id,
        )
        created = create_partner_request(db, request_data)
        
        retrieved = get_partner_request(db, created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id

    def test_accept_partner_request(self, db: Session, test_business, test_partner_profile, test_user):
        """Test accepting a partner request."""
        request_data = PartnerRequestCreate(
            business_id=test_business.id,
            partner_id=test_partner_profile.id,
            requested_by=test_user.id,
        )
        request = create_partner_request(db, request_data)
        
        accepted = accept_partner_request(db, request.id)
        
        assert accepted.status == RequestStatus.ACCEPTED

    def test_reject_partner_request(self, db: Session, test_business, test_partner_profile, test_user):
        """Test rejecting a partner request."""
        request_data = PartnerRequestCreate(
            business_id=test_business.id,
            partner_id=test_partner_profile.id,
            requested_by=test_user.id,
        )
        request = create_partner_request(db, request_data)
        
        rejected = reject_partner_request(db, request.id)
        
        assert rejected.status == RequestStatus.REJECTED

    def test_list_partner_requests_by_business(self, db: Session, test_business, test_user):
        """Test listing partner requests for a business."""
        # Create multiple partner profiles
        for i in range(3):
            user = User(
                id=uuid4(),
                name=f"Partner {i}",
                email=f"partner{i}@example.com",
                password_hash=get_password_hash("pass"),
                role=UserRole.ENTREPRENEUR,
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            profile_data = PartnerProfileCreate(
                user_id=user.id,
                partner_type=PartnerType.MENTOR,
                company_name=f"Partner Co {i}",
            )
            profile = create_partner_profile(db, profile_data)
            
            request_data = PartnerRequestCreate(
                business_id=test_business.id,
                partner_id=profile.id,
                requested_by=test_user.id,
            )
            create_partner_request(db, request_data)
        
        requests = list_partner_requests(db, business_id=test_business.id)
        
        assert len(requests) == 3
        assert all(r.business_id == test_business.id for r in requests)

    def test_list_partner_requests_by_status(self, db: Session, test_business, test_partner_profile, test_user):
        """Test filtering partner requests by status."""
        # Create pending request
        pending_data = PartnerRequestCreate(
            business_id=test_business.id,
            partner_id=test_partner_profile.id,
            requested_by=test_user.id,
        )
        pending = create_partner_request(db, pending_data)
        
        # Create and accept a request
        user2 = User(
            id=uuid4(),
            name="Partner 2",
            email="partner2@example.com",
            password_hash=get_password_hash("pass"),
            role=UserRole.ENTREPRENEUR,
            is_active=True,
        )
        db.add(user2)
        db.commit()
        
        profile2_data = PartnerProfileCreate(
            user_id=user2.id,
            partner_type=PartnerType.INVESTOR,
            company_name="Investor Co",
        )
        profile2 = create_partner_profile(db, profile2_data)
        
        accepted_data = PartnerRequestCreate(
            business_id=test_business.id,
            partner_id=profile2.id,
            requested_by=test_user.id,
        )
        accepted = create_partner_request(db, accepted_data)
        accept_partner_request(db, accepted.id)
        
        # Filter by pending status
        pending_requests = list_partner_requests(db, status=RequestStatus.PENDING)
        
        assert any(r.id == pending.id for r in pending_requests)

    def test_cannot_accept_already_accepted_request(self, db: Session, test_business, test_partner_profile, test_user):
        """Test that already accepted requests cannot be accepted again."""
        request_data = PartnerRequestCreate(
            business_id=test_business.id,
            partner_id=test_partner_profile.id,
            requested_by=test_user.id,
        )
        request = create_partner_request(db, request_data)
        
        accept_partner_request(db, request.id)
        
        with pytest.raises(ValueError, match="already accepted"):
            accept_partner_request(db, request.id)

    def test_partner_request_with_unapproved_profile(self, db: Session, test_business, test_partner_profile, test_user, test_admin):
        """Test requesting a partner with unapproved profile."""
        # Reject the profile
        reject_partner_profile(db, test_partner_profile.id, test_admin.id)
        
        # Should still be able to request, but maybe with warnings
        request_data = PartnerRequestCreate(
            business_id=test_business.id,
            partner_id=test_partner_profile.id,
            requested_by=test_user.id,
        )
        
        # This should work, but the profile is not approved
        request = create_partner_request(db, request_data)
        assert request.id is not None
