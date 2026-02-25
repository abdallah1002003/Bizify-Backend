# ruff: noqa
import sys
from unittest.mock import patch, MagicMock

# Mock the entire redis module BEFORE importing app.core
mock_redis_module = MagicMock()
sys.modules['redis'] = mock_redis_module

import pytest
from app.core.cache import get_cache_manager, clear_cache_manager, InMemoryCache, RedisCache
from config.settings import settings

@pytest.fixture(autouse=True)
def reset_cache_manager():
    """Reset the global cache manager before and after every test to prevent state pollution."""
    clear_cache_manager()
    yield
    clear_cache_manager()

def test_cache_manager_defaults_to_redis_from_settings():
    """Ensure get_cache_manager inherently uses config settings for the Redis parameters."""
    # Temporarily force Redis to be treated as available and healthy
    settings.REDIS_ENABLED = True
    
    mock_instance = MagicMock()
    mock_instance.ping.return_value = True
    mock_redis_module.Redis.return_value = mock_instance
    
    with patch("app.core.cache.redis", new=mock_redis_module):
        # Act
        manager = get_cache_manager()

        # Assert Redis was invoked with correct settings implicitly inside cache.py
        mock_redis_module.Redis.assert_called_once_with(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        db=0,
        decode_responses=False,
        socket_connect_timeout=2,
        socket_keepalive=True
    )
    assert isinstance(manager.backend, RedisCache)

def test_cache_manager_falls_back_to_in_memory_on_redis_failure():
    """Ensure standard graceful degradation to InMemoryCache if Redis crashes."""
    settings.REDIS_ENABLED = True
    
    # Mock an exception when pinging Redis
    mock_instance = MagicMock()
    mock_instance.ping.side_effect = Exception("Connection Refused")
    mock_redis_module.Redis.return_value = mock_instance
    
    with patch("app.core.cache.redis", new=mock_redis_module):
        # Act
        manager = get_cache_manager()
        
        # Assert it gracefully swallowed the error and instantiated InMemoryCache
        assert isinstance(manager.backend, InMemoryCache)

def test_in_memory_cache_operations():
    """Test standard dictionary behaviors for the fallback cache."""
    cache = InMemoryCache()
    assert cache.set("user:1", {"name": "Test"}) is True
    assert cache.get("user:1") == {"name": "Test"}
    assert cache.exists("user:1") is True
    assert cache.delete("user:1") is True
    assert cache.get("user:1") is None
