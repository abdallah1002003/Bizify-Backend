import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.billing.crud_utils import get_by_id, list_records

@pytest.mark.asyncio
async def test_get_by_id():
    mock_db = AsyncMock()
    mock_id = uuid.uuid4()
    mock_model = MagicMock()
    
    # Mock return value
    mock_obj = MagicMock()
    mock_db.get.return_value = mock_obj
    
    result = await get_by_id(mock_db, mock_model, mock_id)
    
    mock_db.get.assert_called_once_with(mock_model, mock_id)
    assert result == mock_obj

@pytest.mark.asyncio
async def test_list_records_no_filters():
    mock_db = AsyncMock()
    mock_model = MagicMock()
    
    # Mock result
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = ["res1", "res2"]
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result
    
    result = await list_records(mock_db, mock_model, skip=10, limit=20)
    
    assert result == ["res1", "res2"]
    # Check if execute was called (stmt construction is verified by the fact it didn't crash and we get result)
    assert mock_db.execute.called

from app.models.billing.billing import Plan

@pytest.mark.asyncio
async def test_list_records_with_filters():
    mock_db = AsyncMock()
    
    plan_id = uuid.uuid4()
    filters = {"id": plan_id, "name": "Premium", "ignored": None}
    
    # Mock result
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result
    
    result = await list_records(mock_db, Plan, filters=filters)
    
    assert result == []
    assert mock_db.execute.called
    # Verify the statement had the where clauses
    args, _ = mock_db.execute.call_args
    stmt = args[0]
    # stmt.whereclause should exist
    assert stmt.whereclause is not None
