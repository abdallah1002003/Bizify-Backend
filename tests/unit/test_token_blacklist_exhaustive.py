import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch, MagicMock
from app.core.token_blacklist import (
    blacklist_token,
    is_token_blacklisted,
    clear_blacklist,
    _get_async_redis_client,
    _memory_store,
)
from config.settings import settings

@pytest.fixture(autouse=True)
def cleanup():
    clear_blacklist()
    # Reset global redis client mock logic if needed
    import app.core.token_blacklist
    app.core.token_blacklist._redis_client = None
    yield
    clear_blacklist()

@pytest.mark.asyncio
async def test_memory_blacklist_basic():
    # Force test mode to use memory
    with patch.object(settings, "APP_ENV", "test"):
        await blacklist_token("jti1", 10)
        assert await is_token_blacklisted("jti1") is True
        assert await is_token_blacklisted("unknown") is False

@pytest.mark.asyncio
async def test_memory_blacklist_expiration():
    with patch.object(settings, "APP_ENV", "test"):
        with patch("time.time", return_value=1000.0):
            await blacklist_token("expired", 10) # expires at 1010
            
        with patch("time.time", return_value=1005.0):
            assert await is_token_blacklisted("expired") is True
            
        with patch("time.time", return_value=1011.0):
            assert await is_token_blacklisted("expired") is False
            assert "expired" not in _memory_store

@pytest.mark.asyncio
async def test_memory_lazy_cleanup():
    with patch.object(settings, "APP_ENV", "test"):
        with patch("time.time", return_value=1000.0):
            await blacklist_token("t1", 5) # 1005
            await blacklist_token("t2", 10) # 1010
            
        assert len(_memory_store) == 2
        
        with patch("time.time", return_value=1006.0):
            await blacklist_token("t3", 10)
            # t1 should be purged during t3 write
            assert "t1" not in _memory_store
            assert "t2" in _memory_store
            assert "t3" in _memory_store

@pytest.mark.asyncio
async def test_blacklist_token_zero_ttl():
    # Should do nothing
    await blacklist_token("jti", 0)
    await blacklist_token("jti", -1)
    assert await is_token_blacklisted("jti") is False

@pytest.mark.asyncio
async def test_redis_client_disabled():
    with patch.object(settings, "REDIS_ENABLED", False):
        client = await _get_async_redis_client()
        assert client is None

@pytest.mark.asyncio
async def test_redis_client_init_success():
    mock_redis = AsyncMock()
    with patch.object(settings, "REDIS_ENABLED", True):
        with patch("redis.asyncio.Redis", return_value=mock_redis):
            client = await _get_async_redis_client()
            assert client == mock_redis
            mock_redis.ping.assert_called_once()
            
            # Hit cached singleton (line 57)
            client2 = await _get_async_redis_client()
            assert client2 is client
            # Ping should not be called again
            assert mock_redis.ping.call_count == 1

@pytest.mark.asyncio
async def test_redis_client_init_failure():
    with patch.object(settings, "REDIS_ENABLED", True):
        with patch("redis.asyncio.Redis", side_effect=Exception("conn error")):
            client = await _get_async_redis_client()
            assert client is None

@pytest.mark.asyncio
async def test_redis_blacklist_success():
    mock_redis = AsyncMock()
    # Mock settings.APP_ENV != "test"
    with patch.object(settings, "APP_ENV", "production"):
        with patch.object(settings, "REDIS_ENABLED", True):
            with patch("app.core.token_blacklist._get_async_redis_client", return_value=mock_redis):
                await blacklist_token("jti_redis", 100)
                mock_redis.setex.assert_called_once_with("jti_blacklist:jti_redis", 100, "1")
                
                mock_redis.exists.return_value = 1
                assert await is_token_blacklisted("jti_redis") is True
                mock_redis.exists.assert_called_once_with("jti_blacklist:jti_redis")

@pytest.mark.asyncio
async def test_redis_fallback_on_exception():
    mock_redis = AsyncMock()
    mock_redis.setex.side_effect = Exception("redis write error")
    mock_redis.exists.side_effect = Exception("redis read error")
    
    with patch.object(settings, "APP_ENV", "production"):
        with patch.object(settings, "REDIS_ENABLED", True):
            with patch("app.core.token_blacklist._get_async_redis_client", return_value=mock_redis):
                # Should fallback to memory on write error
                await blacklist_token("jti_fallback", 100)
                assert await is_token_blacklisted("jti_fallback") is True
                # (is_token_blacklisted will also try redis, fail, and check memory)
                
@pytest.mark.asyncio
async def test_redis_none_client_fallback():
    with patch.object(settings, "APP_ENV", "production"):
        with patch("app.core.token_blacklist._get_async_redis_client", return_value=None):
            await blacklist_token("token1", 60)
            assert await is_token_blacklisted("token1") is True
            # Verified via memory store
            assert "token1" in _memory_store
