import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.billing.payment_method import (
    PaymentMethodService,
    _normalize_provider,
    get_payment_method,
    get_payment_methods,
    create_payment_method,
    update_payment_method,
    delete_payment_method,
)
from app.models import PaymentMethod
from app.core.exceptions import ValidationError

@pytest.fixture
def mock_repo():
    with patch("app.services.billing.payment_method.PaymentMethodRepository") as mock:
        yield mock

@pytest.fixture
def pm_service(mock_repo):
    db = AsyncMock()
    return PaymentMethodService(db)

def test_normalize_provider():
    assert _normalize_provider(" Stripe ") == "stripe"
    with pytest.raises(ValidationError) as exc:
        _normalize_provider(None)
    assert "provider is required" in str(exc.value)

@pytest.mark.asyncio
async def test_pm_service_get_methods(pm_service):
    uid = uuid4()
    pm_service.repo.get_for_user = AsyncMock(return_value=[])
    await pm_service.get_payment_methods(user_id=uid)
    pm_service.repo.get_for_user.assert_called_once_with(uid)
    
    pm_service.repo.get_all = AsyncMock(return_value=[])
    await pm_service.get_payment_methods(skip=0, limit=10)
    pm_service.repo.get_all.assert_called_once_with(skip=0, limit=10)

@pytest.mark.asyncio
async def test_pm_service_get_payment_method(pm_service):
    mock_id = uuid4()
    pm_service.repo.get = AsyncMock(return_value=MagicMock())
    await pm_service.get_payment_method(mock_id)
    pm_service.repo.get.assert_called_once_with(mock_id)

@pytest.mark.asyncio
async def test_pm_service_create_logic(pm_service):
    uid = uuid4()
    
    # Validation error
    with pytest.raises(ValidationError):
        await pm_service.create_payment_method({"provider": "stripe"})

    # First method (auto-default)
    pm_service.repo.get_first_for_user = AsyncMock(return_value=None)
    mock_pm = MagicMock(spec=PaymentMethod)
    mock_pm.is_default = True
    pm_service.repo.create = AsyncMock(return_value=mock_pm)
    pm_service.repo.commit = AsyncMock()
    pm_service.repo.refresh = AsyncMock()
    
    # Mock _unset_other_defaults internals
    pm_service.repo.get_for_user = AsyncMock(return_value=[mock_pm])
    
    result = await pm_service.create_payment_method({"user_id": uid, "provider": "stripe"})
    assert result.is_default is True

    # Subsequent method (explictly default)
    pm_service.repo.get_first_for_user = AsyncMock(return_value=MagicMock())
    result = await pm_service.create_payment_method({"user_id": uid, "provider": "stripe", "is_default": True})
    assert result.is_default is True

@pytest.mark.asyncio
async def test_pm_service_update_logic(pm_service):
    db_obj = MagicMock(spec=PaymentMethod)
    db_obj.id = uuid4()
    db_obj.user_id = uuid4()
    
    pm_service.repo.update = AsyncMock(return_value=db_obj)
    pm_service.repo.commit = AsyncMock()
    pm_service.repo.refresh = AsyncMock()
    pm_service.repo.get_for_user = AsyncMock(return_value=[])
    
    # Update is_default=True
    db_obj.is_default = True
    await pm_service.update_payment_method(db_obj, {"is_default": True, "provider": "STRIPE"})
    pm_service.repo.update.assert_called()

    # Update is_default=False but it's the only one
    db_obj.is_default = False
    pm_service.repo.get_first_for_user = AsyncMock(return_value=db_obj)
    await pm_service.update_payment_method(db_obj, {"is_default": False})
    # Should be set back to True
    pm_service.repo.update.assert_called_with(db_obj, {"is_default": True}, auto_commit=False)

@pytest.mark.asyncio
async def test_pm_service_delete(pm_service):
    mock_id = uuid4()
    pm_service.repo.get = AsyncMock(return_value=None)
    assert await pm_service.delete_payment_method(mock_id) is None
    
    db_obj = MagicMock(spec=PaymentMethod)
    db_obj.user_id = uuid4()
    db_obj.is_default = True
    pm_service.repo.get = AsyncMock(return_value=db_obj)
    pm_service.repo.delete = AsyncMock()
    pm_service.repo.get_first_for_user = AsyncMock(return_value=MagicMock())
    pm_service.repo.update = AsyncMock()
    
    await pm_service.delete_payment_method(mock_id)
    pm_service.repo.update.assert_called_once()
    
    # was_default=False branch
    db_obj.is_default = False
    pm_service.repo.update.reset_mock()
    await pm_service.delete_payment_method(mock_id)
    pm_service.repo.update.assert_not_called()

@pytest.mark.asyncio
async def test_pm_service_misc(pm_service):
    uid = uuid4()
    pm_service.repo.get_default_for_user = AsyncMock()
    await pm_service.get_default_payment_method(uid)
    
    # _unset_other_defaults (118)
    obj = MagicMock(spec=PaymentMethod)
    obj.id = uuid4()
    obj.is_default = True
    pm_service.repo.get_for_user = AsyncMock(return_value=[obj])
    pm_service.repo.update = AsyncMock()
    await pm_service._unset_other_defaults(uid, uuid4())
    assert pm_service.repo.update.called

@pytest.mark.asyncio
async def test_standalone_functions():
    db = AsyncMock()
    mock_id = uuid4()
    uid = uuid4()
    
    # get_payment_method
    db.get = AsyncMock(return_value=None)
    await get_payment_method(db, mock_id)
    
    # get_payment_methods (171-180)
    mock_res = MagicMock()
    mock_res.scalars().all.return_value = []
    db.execute = AsyncMock(return_value=mock_res)
    await get_payment_methods(db, user_id=uid)
    await get_payment_methods(db, user_id=None)
    
    # create_payment_method (188, 195, 204)
    with pytest.raises(ValidationError):
        await create_payment_method(db, {"provider": "stripe", "user_id": None})
        
    mock_res.scalar_one_or_none.return_value = None # No first method
    db.execute = AsyncMock(return_value=mock_res)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.flush = AsyncMock()
    await create_payment_method(db, {"user_id": uid, "provider": "stripe"})
    
    mock_res.scalar_one_or_none.return_value = MagicMock() # Has first method
    await create_payment_method(db, {"user_id": uid, "provider": "stripe", "is_default": True})

    # update_payment_method (215, 225, 227-231)
    db_obj = MagicMock(spec=PaymentMethod)
    db_obj.id = mock_id
    db_obj.user_id = uid
    db_obj.is_default = False
    mock_res.scalar_one_or_none.return_value = db_obj # it's the first method
    db.execute = AsyncMock(return_value=mock_res)
    await update_payment_method(db, db_obj, {"is_default": False, "provider": " STRIPE "})
    assert db_obj.is_default is True
    
    # Cover line 225: updating to default
    db_obj.is_default = True
    await update_payment_method(db, db_obj, {"is_default": True})
    assert db.execute.called # for _unset_other_defaults
    
    # delete_payment_method (242, 246-263)
    db.get = AsyncMock(return_value=None)
    await delete_payment_method(db, mock_id)
    
    db_obj.is_default = True
    col = MagicMock()
    col.name = "id"
    db_obj.__table__.columns = [col]
    db.get = AsyncMock(return_value=db_obj)
    db.delete = AsyncMock()
    mock_res.scalar_one_or_none.return_value = MagicMock() # replacement
    db.execute = AsyncMock(return_value=mock_res)
    await delete_payment_method(db, mock_id)

    # _unset_other_defaults standalone (140-141)
    mock_res.scalars().all.return_value = [db_obj]
    db.execute = AsyncMock(return_value=mock_res)
    from app.services.billing.payment_method import _unset_other_defaults
    await _unset_other_defaults(db, uid, mock_id)
    assert db_obj.is_default is False
