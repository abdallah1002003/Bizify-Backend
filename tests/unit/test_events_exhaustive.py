import pytest
import asyncio
import json
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from app.core import events
from app.core.events import (
    EventDispatcher, 
    CustomJSONEncoder, 
    dispatcher,
)
from app.core.event_handlers import register_all_handlers
from config.settings import settings

@pytest.fixture
def clean_dispatcher():
    # Create a FRESH instance to avoid the global mock in conftest.py
    d = EventDispatcher()
    d.clear_all_handlers()
    yield d
    d.clear_all_handlers()

def test_custom_json_encoder():
    uid = uuid.uuid4()
    now = datetime.now()
    data = {"id": uid, "time": now, "other": 1}
    
    encoded = json.dumps(data, cls=CustomJSONEncoder)
    decoded = json.loads(encoded)
    
    assert decoded["id"] == str(uid)
    assert decoded["time"] == now.isoformat()
    assert decoded["other"] == 1
    
    # Test fallback
    with pytest.raises(TypeError):
        json.dumps({"func": lambda x: x}, cls=CustomJSONEncoder)

@pytest.mark.asyncio
async def test_dispatcher_subscribe_duplicate(clean_dispatcher):
    async def handler(et, p): pass
    
    clean_dispatcher.subscribe("test_event", handler)
    clean_dispatcher.subscribe("test_event", handler) # duplicate
    
    assert len(clean_dispatcher._handlers["test_event"]) == 1

@pytest.mark.asyncio
async def test_dispatcher_emit_test_env(clean_dispatcher):
    mock_handler = AsyncMock()
    clean_dispatcher.subscribe("test_event", mock_handler)
    
    # Directly modify the module-level settings
    old_env = events.settings.APP_ENV
    events.settings.APP_ENV = "test"
    try:
        await clean_dispatcher.emit("test_event", {"foo": "bar"})
    finally:
        events.settings.APP_ENV = old_env
        
    mock_handler.assert_called_once_with("test_event", {"foo": "bar"})

@pytest.mark.asyncio
async def test_dispatcher_emit_redis_path(clean_dispatcher):
    mock_cache = MagicMock()
    mock_client = AsyncMock()
    mock_cache.backend.client = mock_client
    
    old_env = events.settings.APP_ENV
    events.settings.APP_ENV = "production"
    try:
        with patch("app.core.events.get_cache_manager", return_value=mock_cache):
            await clean_dispatcher.emit("prod_event", {"data": 1})
            
            mock_client.lpush.assert_called_once()
            args, _ = mock_client.lpush.call_args
            assert args[0] == "app:event_queue"
    finally:
        events.settings.APP_ENV = old_env

@pytest.mark.asyncio
async def test_dispatcher_emit_redis_failure_fallback(clean_dispatcher):
    mock_cache = MagicMock()
    mock_client = AsyncMock()
    mock_client.lpush.side_effect = Exception("Redis down")
    mock_cache.backend.client = mock_client
    
    mock_handler = AsyncMock()
    clean_dispatcher.subscribe("fallback_event", mock_handler)
    
    old_env = events.settings.APP_ENV
    events.settings.APP_ENV = "production"
    try:
        with patch("app.core.events.get_cache_manager", return_value=mock_cache):
            await clean_dispatcher.emit("fallback_event", {"val": 2})
            mock_handler.assert_called_once_with("fallback_event", {"val": 2})
    finally:
        events.settings.APP_ENV = old_env

@pytest.mark.asyncio
async def test_dispatcher_emit_no_redis_client_fallback(clean_dispatcher):
    mock_cache = MagicMock()
    mock_cache.backend.client = None # No client
    
    mock_handler = AsyncMock()
    clean_dispatcher.subscribe("no_client_event", mock_handler)
    
    old_env = events.settings.APP_ENV
    events.settings.APP_ENV = "production"
    try:
        with patch("app.core.events.get_cache_manager", return_value=mock_cache):
            await clean_dispatcher.emit("no_client_event", {"val": 3})
            mock_handler.assert_called_once()
    finally:
        events.settings.APP_ENV = old_env

@pytest.mark.asyncio
async def test_run_handlers_branches(clean_dispatcher):
    # Case: no handlers for event_type
    await clean_dispatcher._run_handlers("missing_event", {})
    # No error, just returns
    
    # Case: multiple handlers with exceptions
    async def h1(et, p): pass
    async def h2(et, p): raise ValueError("handler fail")
    
    clean_dispatcher.subscribe("multi", h1)
    clean_dispatcher.subscribe("multi", h2)
    
    # asyncio.gather with return_exceptions=True should handle the error
    await clean_dispatcher._run_handlers("multi", {})

def test_global_dispatcher_singleton():
    assert isinstance(dispatcher, EventDispatcher)
    assert dispatcher.queue_key == "app:event_queue"

def test_register_all_handlers():
    with patch("app.core.event_handlers.register_idea_version_handlers") as m1, \
         patch("app.core.event_handlers.register_business_roadmap_handlers") as m2, \
         patch("app.core.event_handlers.register_business_collaborator_handlers") as m3, \
         patch("app.core.event_handlers.register_email_handlers") as m4:
        
        register_all_handlers()
        
        m1.assert_called_once()
        m2.assert_called_once()
        m3.assert_called_once()
        m4.assert_called_once()
