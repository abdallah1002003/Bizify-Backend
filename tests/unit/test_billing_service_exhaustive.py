import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from app.services.billing.billing_service import (
    check_usage_limit,
    record_usage,
    get_usage,
    get_usages,
    create_usage,
    update_usage,
    delete_usage,
    get_detailed_status,
    reset_internal_state,
)

@pytest.fixture
def mock_usage_service():
    with patch("app.services.billing.billing_service.UsageService") as mock:
        yield mock

@pytest.mark.asyncio
async def test_check_usage_limit(mock_usage_service):
    mock_db = AsyncMock()
    user_id = uuid4()
    resource_type = "test_resource"
    
    mock_inst = mock_usage_service.return_value
    mock_inst.check_usage_limit = AsyncMock(return_value=True)
    
    result = await check_usage_limit(mock_db, user_id, resource_type)
    
    assert result is True
    mock_usage_service.assert_called_once_with(mock_db)
    mock_inst.check_usage_limit.assert_called_once_with(user_id, resource_type)

@pytest.mark.asyncio
async def test_record_usage(mock_usage_service):
    mock_db = AsyncMock()
    user_id = uuid4()
    resource_type = "test_resource"
    quantity = 5
    
    mock_usage = MagicMock()
    mock_inst = mock_usage_service.return_value
    mock_inst.record_usage = AsyncMock(return_value=mock_usage)
    
    result = await record_usage(mock_db, user_id, resource_type, quantity)
    
    assert result == mock_usage
    mock_inst.record_usage.assert_called_once_with(user_id, resource_type, quantity)

@pytest.mark.asyncio
async def test_get_usage(mock_usage_service):
    mock_db = AsyncMock()
    usage_id = uuid4()
    
    mock_usage = MagicMock()
    mock_inst = mock_usage_service.return_value
    mock_inst.get_usage = AsyncMock(return_value=mock_usage)
    
    result = await get_usage(mock_db, usage_id)
    
    assert result == mock_usage
    mock_inst.get_usage.assert_called_once_with(usage_id)

@pytest.mark.asyncio
async def test_get_usages(mock_usage_service):
    mock_db = AsyncMock()
    user_id = uuid4()
    
    mock_list = [MagicMock()]
    mock_inst = mock_usage_service.return_value
    mock_inst.get_usages = AsyncMock(return_value=mock_list)
    
    result = await get_usages(mock_db, skip=10, limit=50, user_id=user_id)
    
    assert result == mock_list
    mock_inst.get_usages.assert_called_once_with(skip=10, limit=50, user_id=user_id)

@pytest.mark.asyncio
async def test_create_usage(mock_usage_service):
    mock_db = AsyncMock()
    obj_in = {"foo": "bar"}
    
    mock_usage = MagicMock()
    mock_inst = mock_usage_service.return_value
    mock_inst.create_usage = AsyncMock(return_value=mock_usage)
    
    result = await create_usage(mock_db, obj_in)
    
    assert result == mock_usage
    mock_inst.create_usage.assert_called_once_with(obj_in)

@pytest.mark.asyncio
async def test_update_usage(mock_usage_service):
    mock_db = AsyncMock()
    db_obj = MagicMock()
    obj_in = {"baz": "qux"}
    
    mock_usage = MagicMock()
    mock_inst = mock_usage_service.return_value
    mock_inst.update_usage = AsyncMock(return_value=mock_usage)
    
    result = await update_usage(mock_db, db_obj, obj_in)
    
    assert result == mock_usage
    mock_inst.update_usage.assert_called_once_with(db_obj, obj_in)

@pytest.mark.asyncio
async def test_delete_usage(mock_usage_service):
    mock_db = AsyncMock()
    usage_id = uuid4()
    
    mock_usage = MagicMock()
    mock_inst = mock_usage_service.return_value
    mock_inst.delete_usage = AsyncMock(return_value=mock_usage)
    
    result = await delete_usage(mock_db, usage_id)
    
    assert result == mock_usage
    mock_inst.delete_usage.assert_called_once_with(usage_id)

def test_get_detailed_status():
    status = get_detailed_status()
    assert status["module"] == "billing_service"
    assert status["status"] == "operational"
    assert "timestamp" in status

def test_reset_internal_state():
    with patch("app.services.billing.billing_service.logger") as mock_logger:
        reset_internal_state()
        mock_logger.info.assert_called_once()
