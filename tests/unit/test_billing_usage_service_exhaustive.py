import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.billing.usage_service import (
    UsageService,
    get_usage_service,
    check_usage_limit,
    record_usage,
    get_usage,
    get_usages,
    create_usage,
    update_usage,
    delete_usage,
)
from app.models import Usage
from app.core.exceptions import ValidationError, InvalidStateError

@pytest.fixture
def mock_repo():
    with patch("app.services.billing.usage_service.UsageRepository") as mock:
        yield mock

@pytest.fixture
def usage_service(mock_repo):
    db = AsyncMock()
    return UsageService(db)

def test_normalize_resource_type():
    assert UsageService._normalize_resource_type("  api_calls  ") == "API_CALLS"
    with pytest.raises(ValidationError) as exc:
        UsageService._normalize_resource_type("")
    assert "cannot be empty" in str(exc.value)

def test_validate_quantity():
    assert UsageService._validate_quantity(5) == 5
    with pytest.raises(ValidationError) as exc:
        UsageService._validate_quantity(-1)
    assert "must be non-negative" in str(exc.value)

@pytest.mark.asyncio
async def test_check_usage_limit(usage_service):
    user_id = uuid4()
    
    # Case: usage is None
    usage_service.repo.get_by_resource = AsyncMock(return_value=None)
    assert await usage_service.check_usage_limit(user_id, "TEST") is True
    
    # Case: limit is None
    mock_usage = MagicMock(spec=Usage)
    mock_usage.limit_value = None
    usage_service.repo.get_by_resource = AsyncMock(return_value=mock_usage)
    assert await usage_service.check_usage_limit(user_id, "TEST") is True
    
    # Case: usage < limit
    mock_usage.limit_value = 10
    mock_usage.used = 5
    assert await usage_service.check_usage_limit(user_id, "TEST") is True
    
    # Case: usage >= limit
    mock_usage.used = 10
    assert await usage_service.check_usage_limit(user_id, "TEST") is False

@pytest.mark.asyncio
async def test_record_usage_new_row(usage_service):
    user_id = uuid4()
    usage_service.repo.get_by_resource = AsyncMock(return_value=None)
    
    # Mock db.add and db.commit
    usage_service.db.add = MagicMock()
    usage_service.db.commit = AsyncMock()
    usage_service.db.refresh = AsyncMock()
    
    result = await usage_service.record_usage(user_id, "TEST", 5)
    
    assert result.used == 5
    assert result.resource_type == "TEST"
    usage_service.db.add.assert_called_once()
    usage_service.db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_record_usage_quota_exceeded(usage_service):
    user_id = uuid4()
    mock_usage = MagicMock(spec=Usage)
    mock_usage.used = 8
    mock_usage.limit_value = 10
    usage_service.repo.get_by_resource = AsyncMock(return_value=mock_usage)
    
    with pytest.raises(InvalidStateError) as exc:
        await usage_service.record_usage(user_id, "TEST", 5)
    assert "Usage quota exceeded" in str(exc.value)

@pytest.mark.asyncio
async def test_get_usage(usage_service):
    mock_id = uuid4()
    mock_usage = MagicMock()
    usage_service.db.get = AsyncMock(return_value=mock_usage)
    
    result = await usage_service.get_usage(mock_id)
    assert result == mock_usage
    usage_service.db.get.assert_called_once_with(Usage, mock_id)

@pytest.mark.asyncio
async def test_get_usages(usage_service):
    user_id = uuid4()
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = ["usage1"]
    mock_result.scalars.return_value = mock_scalars
    usage_service.db.execute = AsyncMock(return_value=mock_result)
    
    result = await usage_service.get_usages(user_id=user_id)
    assert result == ["usage1"]
    assert usage_service.db.execute.called

@pytest.mark.asyncio
async def test_create_usage_validation_and_merge(usage_service):
    # Missing required fields
    with pytest.raises(ValidationError) as exc:
        await usage_service.create_usage({})
    assert "required" in str(exc.value)
    
    # Valid data, merge with existing
    user_id = uuid4()
    obj_in = {"user_id": user_id, "resource_type": "TEST", "used": 5, "limit_value": 100}
    
    mock_existing = MagicMock(spec=Usage)
    usage_service.repo.get_by_resource = AsyncMock(return_value=mock_existing)
    usage_service.db.commit = AsyncMock()
    usage_service.db.refresh = AsyncMock()
    
    result = await usage_service.create_usage(obj_in)
    assert result == mock_existing
    usage_service.db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_create_usage_new_row(usage_service):
    user_id = uuid4()
    obj_in = {"user_id": user_id, "resource_type": "TEST", "limit_value": 50}
    usage_service.repo.get_by_resource = AsyncMock(return_value=None)
    
    # Invalid limit_value
    with pytest.raises(ValidationError) as exc:
        await usage_service.create_usage({**obj_in, "limit_value": -1})
    assert "limit_value must be non-negative" in str(exc.value)

    usage_service.db.add = MagicMock()
    usage_service.db.commit = AsyncMock()
    usage_service.db.refresh = AsyncMock()
    
    result = await usage_service.create_usage(obj_in)
    assert result.limit_value == 50
    usage_service.db.add.assert_called_once()

@pytest.mark.asyncio
async def test_update_usage(usage_service):
    db_obj = MagicMock(spec=Usage)
    obj_in = {"used": 20, "resource_type": "new_type", "limit_value": 0}
    
    # Test negative limit_value
    with pytest.raises(ValidationError) as exc:
        await usage_service.update_usage(db_obj, {"limit_value": -10})
    
    usage_service.db.commit = AsyncMock()
    usage_service.db.refresh = AsyncMock()
    
    result = await usage_service.update_usage(db_obj, obj_in)
    assert result == db_obj
    usage_service.db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_delete_usage(usage_service):
    mock_id = uuid4()
    
    # Case: not found
    usage_service.db.get = AsyncMock(return_value=None)
    assert await usage_service.delete_usage(mock_id) is None
    
    # Case: found
    mock_obj = MagicMock()
    usage_service.db.get = AsyncMock(return_value=mock_obj)
    usage_service.db.delete = AsyncMock()
    usage_service.db.commit = AsyncMock()
    
    result = await usage_service.delete_usage(mock_id)
    assert result == mock_obj
    usage_service.db.delete.assert_called_once_with(mock_obj)
    usage_service.db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_get_usage_service():
    db = AsyncMock()
    svc = await get_usage_service(db)
    assert isinstance(svc, UsageService)

@pytest.mark.asyncio
async def test_legacy_aliases(usage_service):
    db = usage_service.db
    mock_id = uuid4()
    
    with patch.object(UsageService, "check_usage_limit", new_callable=AsyncMock) as m:
        await check_usage_limit(db, mock_id, "TEST")
        m.assert_called_once()
        
    with patch.object(UsageService, "record_usage", new_callable=AsyncMock) as m:
        await record_usage(db, mock_id, "TEST", 1)
        m.assert_called_once()
        
    with patch.object(UsageService, "get_usage", new_callable=AsyncMock) as m:
        await get_usage(db, mock_id)
        m.assert_called_once()
        
    with patch.object(UsageService, "get_usages", new_callable=AsyncMock) as m:
        await get_usages(db)
        m.assert_called_once()
        
    with patch.object(UsageService, "create_usage", new_callable=AsyncMock) as m:
        await create_usage(db, {})
        m.assert_called_once()
        
    with patch.object(UsageService, "update_usage", new_callable=AsyncMock) as m:
        await update_usage(db, MagicMock(), {})
        m.assert_called_once()
        
    with patch.object(UsageService, "delete_usage", new_callable=AsyncMock) as m:
        await delete_usage(db, mock_id)
        m.assert_called_once()
