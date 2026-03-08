import pytest
import jwt
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException, status
from app.core.dependencies import (
    get_current_user,
    get_current_active_user,
    require_roles,
    is_admin_or_self,
    require_admin_or_self,
)
from app.models.enums import UserRole
import app.models as models
from config.settings import settings

@pytest.fixture
def mock_user():
    user = MagicMock(spec=models.User)
    user.id = uuid.uuid4()
    user.is_active = True
    user.is_verified = True
    user.role = UserRole.ENTREPRENEUR
    return user

@pytest.mark.asyncio
async def test_get_current_user_success(mock_user):
    token_data = {
        "sub": str(mock_user.id),
        "jti": "jti-123",
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30)
    }
    token = jwt.encode(token_data, settings.jwt_signing_key, algorithm=settings.jwt_algorithm)
    
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_db.execute.return_value = mock_result
    
    with patch("app.core.dependencies.is_token_blacklisted", return_value=False):
        user = await get_current_user(db=mock_db, token=token)
        assert user == mock_user

@pytest.mark.asyncio
async def test_get_current_user_refresh_token_fail():
    token_data = {"type": "refresh", "sub": "1"}
    token = jwt.encode(token_data, settings.jwt_signing_key, algorithm=settings.jwt_algorithm)
    
    with pytest.raises(HTTPException) as exc:
        await get_current_user(db=AsyncMock(), token=token)
    assert exc.value.status_code == 401
    assert "Refresh token" in exc.value.detail

@pytest.mark.asyncio
async def test_get_current_user_revoked_token():
    token_data = {"sub": "1", "jti": "revoked", "type": "access"}
    token = jwt.encode(token_data, settings.jwt_signing_key, algorithm=settings.jwt_algorithm)
    
    with patch("app.core.dependencies.is_token_blacklisted", return_value=True):
        with pytest.raises(HTTPException) as exc:
            await get_current_user(db=AsyncMock(), token=token)
    assert exc.value.status_code == 401
    assert "revoked" in exc.value.detail

@pytest.mark.asyncio
async def test_get_current_user_no_sub():
    token_data = {"type": "access"} # missing sub
    token = jwt.encode(token_data, settings.jwt_signing_key, algorithm=settings.jwt_algorithm)
    
    with pytest.raises(HTTPException) as exc:
        await get_current_user(db=AsyncMock(), token=token)
    assert exc.value.status_code == 401

@pytest.mark.asyncio
async def test_get_current_user_invalid_jwt():
    with pytest.raises(HTTPException):
        await get_current_user(db=AsyncMock(), token="invalid.token")

@pytest.mark.asyncio
async def test_get_current_user_not_in_db():
    token_data = {"sub": "nonexistent", "type": "access"}
    token = jwt.encode(token_data, settings.jwt_signing_key, algorithm=settings.jwt_algorithm)
    
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    
    with pytest.raises(HTTPException) as exc:
        await get_current_user(db=mock_db, token=token)
    assert exc.value.status_code == 401

def test_get_current_active_user_success(mock_user):
    assert get_current_active_user(mock_user) == mock_user

def test_get_current_active_user_inactive(mock_user):
    mock_user.is_active = False
    with pytest.raises(HTTPException) as exc:
        get_current_active_user(mock_user)
    assert exc.value.status_code == 401

def test_get_current_active_user_not_verified():
    mock_user = MagicMock()
    mock_user.is_active = True
    mock_user.is_verified = False
    
    # Case: APP_ENV = test (success)
    with patch.object(settings, "APP_ENV", "test"):
        assert get_current_active_user(mock_user) == mock_user
        
    # Case: APP_ENV = production (fail)
    with patch.object(settings, "APP_ENV", "production"):
        with pytest.raises(HTTPException) as exc:
            get_current_active_user(mock_user)
        assert exc.value.status_code == 403

def test_require_roles_success(mock_user):
    mock_user.role = UserRole.ADMIN
    check = require_roles(UserRole.ADMIN, UserRole.MENTOR)
    # Actually call the sub-dependency check function (line 129)
    # And verify the return value (hits line 135)
    result = check(mock_user)
    assert result == mock_user

def test_require_roles_fail(mock_user):
    mock_user.role = UserRole.ENTREPRENEUR
    check = require_roles(UserRole.ADMIN)
    # Actually call the sub-dependency check function (line 131)
    with pytest.raises(HTTPException) as exc:
        check(mock_user)
    assert exc.value.status_code == 403
    assert "Required role: admin" in exc.value.detail

def test_admin_or_self_logic():
    admin = MagicMock()
    admin.id = uuid.uuid4()
    admin.role = UserRole.ADMIN
    
    user = MagicMock()
    user.id = uuid.uuid4()
    user.role = UserRole.ENTREPRENEUR
    
    other_id = uuid.uuid4()
    
    # Line 146
    assert is_admin_or_self(admin, other_id) is True
    assert is_admin_or_self(user, user.id) is True
    assert is_admin_or_self(user, other_id) is False

def test_require_admin_or_self_exception():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.role = UserRole.ENTREPRENEUR
    
    # Success (Line 152 branch)
    require_admin_or_self(user, user.id)
    
    # Failure (Line 153)
    with pytest.raises(HTTPException) as exc:
        require_admin_or_self(user, uuid.uuid4())
    assert exc.value.status_code == 403
