"""Tests covering the exhaustiveness of UserService and AuthService missing branches."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import uuid
import jwt
from datetime import datetime, timezone

from app.services.users.user_service import UserService, get_user_service
from app.services.auth.auth_service import AuthService, get_auth_service
from app.core.exceptions import AuthenticationError, BadRequestError, ConflictError, ResourceNotFoundError


# ── UserService ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_user_service_exhaustive():
    db = AsyncMock()
    svc = UserService(db)
    svc.user_repo = AsyncMock()
    svc.profile_repo = AsyncMock()
    svc.admin_log_service = AsyncMock()
    uid = uuid.uuid4()
    admin_id = uuid.uuid4()

    # get_user, get_user_by_email, get_users, count_users, has_admin_user
    await svc.get_user(uid)
    svc.user_repo.get_with_profile.assert_called_with(uid)
    await svc.get_user_by_email("a@b.com")
    await svc.get_users(0, 50)
    await svc.count_users()
    await svc.has_admin_user()

    # _record_admin_action: target_id is None -> ValueError
    with pytest.raises(ValueError, match="target_id is required"):
        await svc._record_admin_action(admin_id, "TEST", None)

    # create_user: success path
    svc.user_repo.create.return_value = MagicMock(id=uid, email="a@b.com")
    svc.profile_repo.get_by_user_id.return_value = None
    with patch("app.services.users.user_service.get_password_hash", return_value="hashed_pw"):
        res = await svc.create_user({"email": "a@b.com", "password": "abc"})
        assert res.id == uid
        svc.user_repo.create.assert_called()
        svc.profile_repo.create.assert_called()
        svc.user_repo.commit.assert_called()
        svc.user_repo.refresh.assert_called()

    # create_user: with existing password_hash
    with patch("app.services.users.user_service.get_password_hash", return_value="hashed_pw2"):
        await svc.create_user({"email": "a@b.com", "password_hash": "existing"})

    # create_user: Exception rollback
    svc.user_repo.create.side_effect = Exception("DB error")
    with pytest.raises(Exception, match="DB error"):
        await svc.create_user({"email": "a@b.com"})
    svc.user_repo.rollback.assert_called()
    svc.user_repo.create.side_effect = None

    # update_user
    db_obj = MagicMock(id=uid)
    with patch("app.services.users.user_service.get_password_hash", return_value="hashed_pw"):
        await svc.update_user(db_obj, {"password": "abc"})
        await svc.update_user(db_obj, {"password_hash": "abc"})
    svc.user_repo.update.assert_called()

    # delete_user
    with patch.object(svc, "get_user", return_value=None):
        assert await svc.delete_user(uid) is None
    with patch.object(svc, "get_user", return_value=db_obj):
        await svc.delete_user(uid)
        svc.admin_log_service.create_admin_action_log.assert_called()
        svc.user_repo.delete.assert_called_with(uid)

    # get_user_profile
    await svc.get_user_profile(id=uid)
    svc.profile_repo.get.assert_called_with(uid)
    await svc.get_user_profile(user_id=uid)
    svc.profile_repo.get_by_user_id.assert_called_with(uid)
    assert await svc.get_user_profile() is None

    # get_user_profiles, create_user_profile
    await svc.get_user_profiles()
    await svc.create_user_profile({"user_id": uid})

    # update_user_profile
    prof_obj = MagicMock(user_id=uid)
    await svc.update_user_profile(prof_obj, {"bio": "test"})
    await svc.update_user_profile(prof_obj, {"bio": "test"}, performer_id=admin_id)
    svc.admin_log_service.create_admin_action_log.assert_called()

    # update_user_profile_by_user_id
    with patch.object(svc, "get_user_profile", return_value=None):
        svc.profile_repo.create.return_value = prof_obj
        await svc.update_user_profile_by_user_id(uid, {"bio": "test2"})
        svc.profile_repo.create.assert_called()
    with patch.object(svc, "get_user_profile", return_value=prof_obj):
        await svc.update_user_profile_by_user_id(uid, {"bio": "test2"}, performer_id=admin_id)

    # delete_user_profile
    with patch.object(svc, "get_user_profile", return_value=None):
        assert await svc.delete_user_profile(uid) is None
    with patch.object(svc, "get_user_profile", return_value=prof_obj):
        await svc.delete_user_profile(uid)
        svc.profile_repo.delete.assert_called_with(prof_obj)

    # admin action log crud
    await svc.get_admin_action_log(uid)
    await svc.get_admin_action_logs()
    await svc.create_admin_action_log({"action": "TEST"})
    await svc.update_admin_action_log(MagicMock(), {"action": "T2"})
    await svc.delete_admin_action_log(uid)

    # dependency
    await get_user_service(db)


# ── AuthService ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_auth_service_exhaustive():
    db = AsyncMock()
    user_svc = AsyncMock()
    svc = AuthService(db, user_svc)
    svc.refresh_token_repo = AsyncMock()
    svc.email_verification_repo = AsyncMock()
    svc.password_reset_repo = AsyncMock()
    uid = uuid.uuid4()

    # _persist_refresh_token
    with patch("jwt.decode", side_effect=jwt.PyJWTError("err")):
        with pytest.raises(AuthenticationError, match="Invalid refresh token"):
            await svc._persist_refresh_token(uid, "token")
            
    with patch("jwt.decode", return_value={"jti": "j", "exp": 1700000000}):
        await svc._persist_refresh_token(uid, "token")
        svc.refresh_token_repo.create.assert_called()

    # refresh_access_token
    # invalid type
    with patch("jwt.decode", return_value={"type": "access", "sub": str(uid), "jti": "j"}):
        with pytest.raises(AuthenticationError, match="Invalid token type"):
            await svc.refresh_access_token("token")
    # missing sub
    with patch("jwt.decode", return_value={"type": "refresh", "jti": "j"}):
        with pytest.raises(AuthenticationError, match="Invalid token payload"):
            await svc.refresh_access_token("token")
    # pyjwt error
    with patch("jwt.decode", side_effect=jwt.PyJWTError("err")):
        with pytest.raises(AuthenticationError, match="Could not validate refresh token"):
            await svc.refresh_access_token("token")
    # missing user or inactive
    with patch("jwt.decode", return_value={"type": "refresh", "sub": str(uid), "jti": "j"}):
        user_svc.get_user.return_value = None
        with pytest.raises(AuthenticationError, match="Inactive or non-existent user"):
            await svc.refresh_access_token("token")
        
        user_svc.get_user.return_value = MagicMock(is_active=False)
        with pytest.raises(AuthenticationError, match="Inactive or non-existent user"):
            await svc.refresh_access_token("token")
            
    # missing jti
    with patch("jwt.decode", return_value={"type": "refresh", "sub": str(uid)}):
        user_svc.get_user.return_value = MagicMock(is_active=True)
        with pytest.raises(AuthenticationError, match="Invalid token payload"):
            await svc.refresh_access_token("token")
            
    # token revoked
    with patch("jwt.decode", return_value={"type": "refresh", "sub": str(uid), "jti": "j"}):
        user_svc.get_user.return_value = MagicMock(id=uid, is_active=True)
        svc.refresh_token_repo.get_by_jti.return_value = MagicMock(revoked=True)
        with pytest.raises(AuthenticationError, match="Token has been revoked"):
            await svc.refresh_access_token("token")
            
    # revoke_refresh_token
    with patch("jwt.decode", side_effect=jwt.PyJWTError("err")):
        await svc.revoke_refresh_token("token") # Doesn't raise
    
    with patch("jwt.decode", return_value={"jti": "j"}):
        svc.refresh_token_repo.revoke.return_value = True
        with patch("app.services.auth.auth_service.active_sessions.dec") as mock_dec:
            await svc.revoke_refresh_token("token")
            mock_dec.assert_called()

    # create_verification_token
    with patch("app.services.auth.auth_service.security.create_email_verification_token", return_value="vtok"), \
         patch("app.services.auth.auth_service.dispatcher.emit", new_callable=AsyncMock) as mock_emit, \
         patch("jwt.decode", return_value={"jti": "j", "exp": 1700000000}):
         await svc.create_verification_token(uid, "o@test.com")
         svc.email_verification_repo.create.assert_called()
         mock_emit.assert_called()

    # verify_email
    with patch("app.services.auth.auth_service.security.verify_email_verification_token", return_value=None):
        with pytest.raises(BadRequestError, match="Invalid or expired verification token"):
            await svc.verify_email("tok")
            
    token_payload_no_sub = {"jti": "j"}
    with patch("app.services.auth.auth_service.security.verify_email_verification_token", return_value=token_payload_no_sub):
        with pytest.raises(BadRequestError, match="Invalid token payload"):
            await svc.verify_email("tok")
            
    token_payload_no_jti = {"sub": "o@test.com"}
    with patch("app.services.auth.auth_service.security.verify_email_verification_token", return_value=token_payload_no_jti):
        with pytest.raises(BadRequestError, match="Invalid token payload"):
            await svc.verify_email("tok")

    token_payload_valid = {"sub": "o@test.com", "jti": "j", "exp": int(datetime.now(timezone.utc).timestamp()) + 3600}
    with patch("app.services.auth.auth_service.security.verify_email_verification_token", return_value=token_payload_valid), \
         patch("app.services.auth.auth_service.is_token_blacklisted", new_callable=AsyncMock, return_value=True):
        with pytest.raises(BadRequestError, match="Verification link has already been used"):
            await svc.verify_email("tok")
            
    with patch("app.services.auth.auth_service.security.verify_email_verification_token", return_value=token_payload_valid), \
         patch("app.services.auth.auth_service.is_token_blacklisted", new_callable=AsyncMock, return_value=False):
        
        # no stored token
        svc.email_verification_repo.get_by_jti.return_value = None
        with pytest.raises(BadRequestError, match="already been used or is invalid"):
            await svc.verify_email("tok")
            
        # no user
        svc.email_verification_repo.get_by_jti.return_value = MagicMock(used=False)
        user_svc.get_user_by_email.return_value = None
        with pytest.raises(ResourceNotFoundError):
            await svc.verify_email("tok")
            
        # user valid but already verified
        user_svc.get_user_by_email.return_value = MagicMock(is_verified=True)
        with patch("app.services.auth.auth_service.blacklist_token", new_callable=AsyncMock) as _m_bl:
            res = await svc.verify_email("tok")
            assert res.is_verified is True
            _m_bl.assert_called()
            
        # user valid not verified
        mock_user = MagicMock(is_verified=False)
        user_svc.get_user_by_email.return_value = mock_user
        with patch("app.services.auth.auth_service.blacklist_token", new_callable=AsyncMock) as _m_bl2:
            await svc.verify_email("tok")
            user_svc.update_user.assert_called_with(mock_user, {"is_verified": True})

    # request_password_reset
    user_svc.get_user_by_email.return_value = None
    assert await svc.request_password_reset("o@t.com") is None
    
    user_svc.get_user_by_email.return_value = MagicMock(id=uid, email="o@t.com")
    with patch("app.services.auth.auth_service.security.create_password_reset_token", return_value="tok"), \
         patch("jwt.decode", return_value={"jti": "j", "exp": 1700000000}), \
         patch("app.services.auth.auth_service.dispatcher.emit", new_callable=AsyncMock):
         await svc.request_password_reset("o@t.com")
         svc.password_reset_repo.create.assert_called()

    # bootstrap_admin
    user_svc.has_admin_user.return_value = True
    with pytest.raises(ConflictError, match="Admin account already exists"):
        await svc.bootstrap_admin("n", "e", "p")

    user_svc.has_admin_user.return_value = False
    user_svc.get_user_by_email.return_value = MagicMock()
    with pytest.raises(ConflictError, match="Email already registered"):
        await svc.bootstrap_admin("n", "e", "p")
        
    user_svc.get_user_by_email.return_value = None
    user_svc.create_user.return_value = MagicMock()
    await svc.bootstrap_admin("n", "e", "p")
    user_svc.create_user.assert_called()

    # reset_password
    with patch("app.services.auth.auth_service.security.verify_password_reset_token", return_value=None):
        with pytest.raises(BadRequestError, match="Invalid or expired reset token"):
            await svc.reset_password("tok", "new")
    
    with patch("app.services.auth.auth_service.security.verify_password_reset_token", return_value={"jti": "j"}):
        with pytest.raises(BadRequestError, match="Invalid reset token subject"):
            await svc.reset_password("tok", "new")
            
    with patch("app.services.auth.auth_service.security.verify_password_reset_token", return_value={"sub": "o@t.com"}):
        with pytest.raises(BadRequestError, match="Invalid reset token identifier"):
            await svc.reset_password("tok", "new")
            
    payload = {"sub": "o@t.com", "jti": "j", "exp": int(datetime.now(timezone.utc).timestamp()) + 3600}
    with patch("app.services.auth.auth_service.security.verify_password_reset_token", return_value=payload):
        with patch("app.services.auth.auth_service.is_token_blacklisted", new_callable=AsyncMock, return_value=True):
            with pytest.raises(BadRequestError, match="Token has already been used"):
                await svc.reset_password("tok", "new")
                
        with patch("app.services.auth.auth_service.is_token_blacklisted", new_callable=AsyncMock, return_value=False):
            svc.password_reset_repo.get_by_jti.return_value = None
            with pytest.raises(BadRequestError, match="already been used or is invalid"):
                await svc.reset_password("tok", "new")
                
            svc.password_reset_repo.get_by_jti.return_value = MagicMock(used=False)
            user_svc.get_user_by_email.return_value = None
            with pytest.raises(ResourceNotFoundError):
                await svc.reset_password("tok", "new")
                
            mock_user = MagicMock()
            user_svc.get_user_by_email.return_value = mock_user
            with patch("app.services.auth.auth_service.blacklist_token", new_callable=AsyncMock):
                await svc.reset_password("tok", "new")
                user_svc.update_user.assert_called_with(mock_user, {"password": "new"})
                
    # dependency
    await get_auth_service(db)
