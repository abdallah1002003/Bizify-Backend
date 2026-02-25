import pytest
from uuid import uuid4
from sqlalchemy.orm import Session
from app.services.users.user_service import UserService, get_user, update_user

def test_record_admin_action_no_target_id(db: Session):
    svc = UserService(db)
    with pytest.raises(ValueError, match="target_id is required for admin log"):
        svc._record_admin_action(admin_id=uuid4(), action_type="TEST", target_id=None)

def test_create_user_with_password_hash(db: Session):
    svc = UserService(db)
    user = svc.create_user({"email": f"testhash{uuid4()}@ex.com", "name": f"user{uuid4()}", "password_hash": "myhash"})
    assert user.password_hash is not None
    assert user.password_hash != "myhash" # It gets hashed again

def test_create_user_exception_rollback(db: Session):
    svc = UserService(db)
    # Trying to create a user with invalid data type or missing non-nullable constraint (like email null if it was possible)
    # We will mock the add method to force an exception
    from unittest.mock import patch
    with patch.object(db, "add", side_effect=Exception("DB Error")):
        with pytest.raises(Exception, match="DB Error"):
            svc.create_user({"email": "fail@ex.com", "password": "abc"})

def test_update_user_with_password_hash(db: Session, test_user):
    svc = UserService(db)
    updated = svc.update_user(test_user, {"password_hash": "newhash"})
    assert updated.password_hash is not None
    assert updated.password_hash != "newhash" # It gets hashed again

def test_update_user_profile_no_performer(db: Session, test_user):
    svc = UserService(db)
    # Ensure profile exists since the fixture might not create it automatically
    profile = svc.get_user_profile(user_id=test_user.id)
    if not profile:
        profile = svc.create_user_profile({"user_id": test_user.id, "bio": "old bio"})
    
    # Updating without performer_id should not create an admin log
    updated = svc.update_user_profile(profile, {"bio": "Updated Bio"}, performer_id=None)
    assert updated.bio == "Updated Bio"

def test_admin_action_log_crud(db: Session, test_user):
    svc = UserService(db)
    # Create
    log = svc.create_admin_action_log({
        "admin_id": test_user.id,
        "action_type": "TEST_ACTION",
        "target_entity": "system",
        "target_id": test_user.id
    })
    assert log.id is not None
    assert log.action_type == "TEST_ACTION"

    # Update
    updated_log = svc.update_admin_action_log(log, {"action_type": "UPDATED_TEST_ACTION"})
    assert updated_log.action_type == "UPDATED_TEST_ACTION"

    # Delete
    deleted_log = svc.delete_admin_action_log(log.id)
    assert deleted_log is not None
    assert svc.get_admin_action_log(log.id) is None

    # Delete non-existent
    assert svc.delete_admin_action_log(uuid4()) is None

def test_legacy_functions(db: Session, test_user):
    user = get_user(db, test_user.id)
    assert user is not None
    assert user.id == test_user.id

    new_name = f"legacy{uuid4().hex[:8]}"
    updated = update_user(db, user, {"name": new_name})
    assert updated.name == new_name

def test_missing_user_crud(db: Session, test_user):
    from app.services.users.user_service import get_user_service, create_user as legacy_create
    svc = UserService(db)
    
    # get_user_by_email
    found = svc.get_user_by_email(test_user.email)
    assert found is not None
    assert found.id == test_user.id
    
    # get_users
    users_list = svc.get_users(skip=0, limit=10)
    assert len(users_list) >= 1
    
    # auto_commit=False branch in _record_admin_action
    log = svc._record_admin_action(admin_id=test_user.id, action_type="NO_COMMIT", target_id=test_user.id, auto_commit=False)
    assert log.action_type == "NO_COMMIT"
    
    # update_user with raw password
    updated_pwd = svc.update_user(test_user, {"password": "rawpassword"})
    assert updated_pwd.password_hash is not None
    
    # Legacy aliases
    legacy_usr = legacy_create(db, {"email": f"leg{uuid4()}@ex.com", "name": "leg", "password": "abc"})
    assert legacy_usr is not None
    assert get_user_service(db) is not None

def test_missing_profile_crud(db: Session, test_user):
    svc = UserService(db)
    
    # Create profile
    prof = svc.create_user_profile({"user_id": test_user.id, "bio": "Initial"})
    
    # get_user_profile branches
    assert svc.get_user_profile(id=prof.id) is not None
    
    # get_user_profiles
    profs = svc.get_user_profiles()
    assert len(profs) >= 1
    
    # update_user_profile with performer_id
    svc.update_user_profile(prof, {"bio": "perform"}, performer_id=test_user.id)
    
    # update_user_profile_by_user_id (existing)
    svc.update_user_profile_by_user_id(test_user.id, {"bio": "by_user"}, performer_id=test_user.id)
    
    # update_user_profile_by_user_id (new creation branch — needs a real user to satisfy the FK)
    import uuid
    from app.core.security import get_password_hash as _hash
    import app.models as _models
    ghost_user = _models.User(
        email=f"ghost_{uuid.uuid4().hex[:8]}@ex.com",
        password_hash=_hash("ghostpass"),
        name="Ghost User",
        role="entrepreneur",
        is_active=True,
        is_verified=True,
    )
    db.add(ghost_user)
    db.commit()
    db.refresh(ghost_user)
    new_prof = svc.update_user_profile_by_user_id(ghost_user.id, {"bio": "brand new"}, performer_id=test_user.id)
    assert new_prof is not None
    
    # delete_user_profile
    deleted = svc.delete_user_profile(prof.id)
    assert deleted is not None
    assert svc.delete_user_profile(uuid.uuid4()) is None

def test_delete_user(db: Session):
    svc = UserService(db)
    u = svc.create_user({"email": f"del{uuid4()}@ex.com", "name": "del", "password": "123"})
    assert svc.delete_user(u.id) is not None
    assert svc.delete_user(uuid4()) is None

def test_get_admin_action_logs(db: Session):
    svc = UserService(db)
    logs = svc.get_admin_action_logs()
    assert isinstance(logs, list)

def test_ultimate_edge_cases(db: Session, test_user):
    svc = UserService(db)
    # Line 146
    assert svc.get_user_profile() is None
    
    # Line 288
    from app.services.users.user_service import update_user as legacy_update
    updated = legacy_update(db, test_user, {"name": "Legacy Update"})
    assert updated.name == "Legacy Update"
