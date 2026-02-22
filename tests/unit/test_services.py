from sqlalchemy.orm import Session
from app.services.users import user_service
from app.services.business import business_invite_service
from app.schemas.users.user import UserCreate
from app.schemas.business.business_invite import BusinessInviteCreate, BusinessInviteUpdate
from app.models.enums import InviteStatus, CollaboratorRole
from app.models import User, Business, BusinessCollaborator
from app.core.security import verify_password
import uuid

def test_create_user_hashes_password(db: Session):
    user_in = UserCreate(
        email="service_test@example.com",
        password="plainpassword",
        name="Service Test",
        role="entrepreneur"
    )
    user = user_service.create_user(db, user_in)
    assert user.email == "service_test@example.com"
    assert verify_password("plainpassword", user.password_hash)
    assert user.password_hash != "plainpassword"

def test_accept_invite_creates_collaborator(db: Session):
    # 1. Create a user
    user = User(
        id=uuid.uuid4(),
        email="invite_test@example.com",
        password_hash="hash",
        name="Invite Test",
        role="entrepreneur",
        is_verified=True
    )
    db.add(user)
    
    # 2. Create a business
    biz = Business(
        id=uuid.uuid4(),
        stage="EARLY",
        owner_id=user.id
    )
    db.add(biz)
    db.commit()

    # 3. Create an invite
    invite_in = BusinessInviteCreate(
        business_id=biz.id,
        email="invite_test@example.com",
        status=InviteStatus.PENDING,
        token="test-token-123",
        invited_by=user.id
    )
    invite = business_invite_service.create_business_invite(db, invite_in)
    
    # 4. Update invite to ACCEPTED
    invite_update = BusinessInviteUpdate(status=InviteStatus.ACCEPTED)
    updated_invite = business_invite_service.update_business_invite(db, invite, invite_update)
    
    assert updated_invite.status == InviteStatus.ACCEPTED
    
    # 5. Check if collaborator was created
    collaborator = db.query(BusinessCollaborator).filter(
        BusinessCollaborator.business_id == biz.id,
        BusinessCollaborator.user_id == user.id
    ).first()
    
    assert collaborator is not None
    assert collaborator.role == CollaboratorRole.VIEWER
