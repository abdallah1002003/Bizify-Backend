import pytest
from uuid import uuid4
from app.services.auth.auth_service import AuthService
import app.models as models
from app.core import security

from app.services.users.user_service import UserService

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

@pytest_asyncio.fixture
async def auth_service(async_db: AsyncSession):
    user_service = UserService(async_db)
    return AuthService(async_db, user_service)

@pytest.mark.asyncio
async def test_auth_service_user_registration(auth_service, async_db):
    email = f"test-{uuid4()}@example.com"
    user = await auth_service.users.create_user({"email": email, "password": "password123", "name": "Test User"})
    
    assert user.email == email
    assert security.verify_password("password123", user.password_hash)
    assert user.is_active is True
    assert user.is_verified is False

@pytest.mark.asyncio
async def test_auth_service_duplicate_registration(auth_service, async_db):
    email = f"dup-{uuid4()}@example.com"
    await auth_service.users.create_user({"email": email, "password": "password", "name": "User 1"})
    
    with pytest.raises(Exception):
        await auth_service.users.create_user({"email": email, "password": "password", "name": "User 2"})

@pytest.mark.asyncio
async def test_auth_service_verify_email(auth_service, async_db):
    email = f"verify-{uuid4()}@example.com"
    user = await auth_service.users.create_user({"email": email, "password": "password", "name": "User"})
    
    # Corrected signature: user_id, email
    token = await auth_service.create_verification_token(user.id, user.email)
    
    # Verify
    verified_user = await auth_service.verify_email(token)
    assert verified_user.id == user.id
    assert verified_user.is_verified is True

@pytest.mark.asyncio
async def test_auth_service_invalid_verify_token(auth_service):
    with pytest.raises(Exception):
        await auth_service.verify_email("invalid-token")

@pytest.mark.asyncio
async def test_auth_service_password_reset_flow(auth_service, async_db):
    email = f"reset-{uuid4()}@example.com"
    user = await auth_service.users.create_user({"email": email, "password": "old-password", "name": "User"})
    
    # Request reset
    await auth_service.request_password_reset(email)
    
    # Get token from DB
    from sqlalchemy import select
    stmt = select(models.PasswordResetToken).where(models.PasswordResetToken.user_id == user.id)
    result = await async_db.execute(stmt)
    reset_token = result.scalar_one_or_none()
    assert reset_token is not None
    
    # Token is blacklisted/used check (this is in router, service just generates it)
    pass
