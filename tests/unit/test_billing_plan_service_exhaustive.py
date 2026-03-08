import pytest
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.billing.plan_service import (
    PlanService,
    get_plan_service,
    get_plan,
    get_plans,
    create_plan,
    update_plan,
    delete_plan,
)
from app.core.exceptions import ValidationError

@pytest.fixture
def mock_repo():
    with patch("app.services.billing.plan_service.PlanRepository") as mock:
        yield mock

@pytest.fixture
def plan_service(mock_repo):
    db = AsyncMock()
    return PlanService(db)

def test_normalize_billing_cycle():
    assert PlanService._normalize_billing_cycle("monthly") == "month"
    assert PlanService._normalize_billing_cycle("YEARLY") == "year"
    assert PlanService._normalize_billing_cycle(None) == "month"
    assert PlanService._normalize_billing_cycle("  annual  ") == "year"
    
    with pytest.raises(ValidationError) as excinfo:
        PlanService._normalize_billing_cycle("daily")
    assert "Unsupported billing_cycle" in str(excinfo.value)

def test_derive_default_ai_runs():
    assert PlanService._derive_default_ai_runs("FREE") == 10
    assert PlanService._derive_default_ai_runs("PRO") == 100
    assert PlanService._derive_default_ai_runs("ENTERPRISE") == 1000
    assert PlanService._derive_default_ai_runs("UNKNOWN") == 10

def test_normalize_payload_name_validation():
    # Empty name
    with pytest.raises(ValidationError) as exc:
        PlanService._normalize_payload({"name": "  "})
    assert "Plan name cannot be empty" in str(exc.value)
    
    # Valid name
    payload = {"name": "  Pro Plan  "}
    normalized = PlanService._normalize_payload(payload)
    assert normalized["name"] == "Pro Plan"

def test_normalize_payload_price_validation():
    # Invalid format
    with pytest.raises(ValidationError) as exc:
        PlanService._normalize_payload({"price": "abc"})
    assert "Invalid price format" in str(exc.value)
    
    # Negative price
    with pytest.raises(ValidationError) as exc:
        PlanService._normalize_payload({"price": -10})
    assert "Plan price must be non-negative" in str(exc.value)
    
    # Valid price
    normalized = PlanService._normalize_payload({"price": "19.99"})
    assert normalized["price"] == Decimal("19.99")

def test_normalize_payload_features_validation():
    # Invalid features_json type
    with pytest.raises(ValidationError) as exc:
        PlanService._normalize_payload({"features_json": "not a dict"})
    assert "must be a dictionary" in str(exc.value)
    
    # Missing ai_runs in features_json
    normalized = PlanService._normalize_payload({"name": "PRO", "features_json": {}})
    assert normalized["features_json"]["ai_runs"] == 100
    
    # Provided ai_runs
    normalized = PlanService._normalize_payload({"features_json": {"ai_runs": 500}})
    assert normalized["features_json"]["ai_runs"] == 500
    
    # None features_json
    normalized = PlanService._normalize_payload({"features_json": None})
    assert normalized["features_json"] == {"ai_runs": 10}

@pytest.mark.asyncio
async def test_get_plan(plan_service, mock_repo):
    mock_id = uuid4()
    mock_plan = MagicMock()
    plan_service.repo.get = AsyncMock(return_value=mock_plan)
    
    result = await plan_service.get_plan(mock_id)
    assert result == mock_plan
    plan_service.repo.get.assert_called_once_with(mock_id)

@pytest.mark.asyncio
async def test_get_plans(plan_service, mock_repo):
    mock_list = [MagicMock()]
    plan_service.repo.get_ordered = AsyncMock(return_value=mock_list)
    
    result = await plan_service.get_plans(skip=5, limit=10)
    assert result == mock_list
    plan_service.repo.get_ordered.assert_called_once_with(skip=5, limit=10)

@pytest.mark.asyncio
async def test_count_plans(plan_service, mock_repo):
    plan_service.repo.count = AsyncMock(return_value=42)
    result = await plan_service.count_plans()
    assert result == 42

@pytest.mark.asyncio
async def test_create_plan_success(plan_service, mock_repo):
    obj_in = {"name": "New Plan", "price": 20}
    
    plan_service.repo.get_by_name = AsyncMock(return_value=None)
    mock_result = MagicMock()
    plan_service.repo.create = AsyncMock(return_value=mock_result)
    
    result = await plan_service.create_plan(obj_in)
    assert result == mock_result

@pytest.mark.asyncio
async def test_create_plan_duplicate(plan_service, mock_repo):
    obj_in = {"name": "Existing"}
    plan_service.repo.get_by_name = AsyncMock(return_value=MagicMock())
    
    with pytest.raises(ValidationError) as exc:
        await plan_service.create_plan(obj_in)
    assert "already exists" in str(exc.value)

@pytest.mark.asyncio
async def test_update_plan_success(plan_service, mock_repo):
    db_obj = MagicMock()
    db_obj.id = uuid4()
    obj_in = {"name": "Updated Name"}
    
    plan_service.repo.get_by_name_excluding = AsyncMock(return_value=None)
    mock_result = MagicMock()
    plan_service.repo.update = AsyncMock(return_value=mock_result)
    
    result = await plan_service.update_plan(db_obj, obj_in)
    assert result == mock_result

@pytest.mark.asyncio
async def test_update_plan_duplicate_name(plan_service, mock_repo):
    db_obj = MagicMock()
    db_obj.id = uuid4()
    obj_in = {"name": "Taken"}
    
    plan_service.repo.get_by_name_excluding = AsyncMock(return_value=MagicMock())
    
    with pytest.raises(ValidationError) as exc:
        await plan_service.update_plan(db_obj, obj_in)
    assert "already exists" in str(exc.value)

@pytest.mark.asyncio
async def test_delete_plan(plan_service, mock_repo):
    mock_id = uuid4()
    plan_service.repo.delete = AsyncMock(return_value=MagicMock())
    result = await plan_service.delete_plan(mock_id)
    assert result is not None

@pytest.mark.asyncio
async def test_get_plan_service():
    db = AsyncMock()
    svc = await get_plan_service(db)
    assert isinstance(svc, PlanService)

@pytest.mark.asyncio
async def test_legacy_aliases():
    db = AsyncMock()
    mock_id = uuid4()
    with patch.object(PlanService, "get_plan", new_callable=AsyncMock) as m:
        await get_plan(db, mock_id)
        m.assert_called_once_with(mock_id)
    
    with patch.object(PlanService, "get_plans", new_callable=AsyncMock) as m:
        await get_plans(db, 0, 10)
        m.assert_called_once_with(0, 10)
    
    with patch.object(PlanService, "create_plan", new_callable=AsyncMock) as m:
        await create_plan(db, {})
        m.assert_called_once()

    with patch.object(PlanService, "update_plan", new_callable=AsyncMock) as m:
        await update_plan(db, MagicMock(), {})
        m.assert_called_once()

    with patch.object(PlanService, "delete_plan", new_callable=AsyncMock) as m:
        await delete_plan(db, mock_id)
        m.assert_called_once_with(mock_id)
