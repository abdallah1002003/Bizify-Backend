import pytest
import asyncio
import zlib
import pickle
import json
from unittest.mock import AsyncMock, MagicMock, patch
from time import time
from app.core.cache import (
    InMemoryCache,
    RedisCache,
    CacheManager,
    get_cache_manager,
    clear_cache_manager,
    CacheBackend
)

@pytest.fixture(autouse=True)
def cleanup_cache():
    clear_cache_manager()
    yield

# ============================================================================
# InMemoryCache Tests
# ============================================================================

@pytest.mark.asyncio
async def test_in_memory_cache_basic():
    cache = InMemoryCache()
    
    # Set and Get
    await cache.set("k1", "v1")
    assert await cache.get("k1") == "v1"
    assert await cache.exists("k1") is True
    
    # Delete
    assert await cache.delete("k1") is True
    assert await cache.get("k1") is None
    assert await cache.delete("unknown") is False
    
    # Clear
    await cache.set("k2", "v2")
    await cache.clear()
    assert await cache.get("k2") is None

@pytest.mark.asyncio
async def test_in_memory_cache_expiration():
    cache = InMemoryCache()
    
    # Use consistent time for set
    with patch("app.core.cache.time", return_value=1000.0):
        await cache.set("short", "life", ttl_seconds=10)
    
    with patch("app.core.cache.time", return_value=1005.0):
        assert await cache.get("short") == "life"
        assert await cache.exists("short") is True

    with patch("app.core.cache.time", return_value=1011.0):
        assert await cache.get("short") is None
        assert await cache.exists("short") is False
        
    # Test exists expiration branch
    with patch("app.core.cache.time", return_value=2000.0):
        await cache.set("ex", "val", ttl_seconds=5)
    
    with patch("app.core.cache.time", return_value=2006.0):
        assert await cache.exists("ex") is False

@pytest.mark.asyncio
async def test_in_memory_cache_stats():
    cache = InMemoryCache()
    await cache.get("miss")
    await cache.set("k1", "v1")
    await cache.get("k1")
    
    stats = cache.get_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["hit_rate"] == 0.5
    assert stats["size"] == 1
    
    assert await cache.health_check() is True

@pytest.mark.asyncio
async def test_cache_backend_abstract_methods():
    # To cover partial pass statements in abstract base class
    class DummyBackend(CacheBackend):
        async def get(self, k): return await super().get(k)
        async def set(self, k, v, t=None): return await super().set(k, v, t)
        async def delete(self, k): return await super().delete(k)
        async def exists(self, k): return await super().exists(k)
        async def clear(self): return await super().clear()
        async def health_check(self): return await super().health_check()
        
    dummy = DummyBackend()
    await dummy.get("k")
    await dummy.set("k", "v")
    await dummy.delete("k")
    await dummy.exists("k")
    await dummy.clear()
    await dummy.health_check()

# ============================================================================
# RedisCache Tests
# ============================================================================

@pytest.mark.asyncio
async def test_redis_cache_init_failure():
    with patch("redis.asyncio.Redis", side_effect=Exception("connection failed")):
        cache = RedisCache()
        assert cache._healthy is False
        assert cache.client is None

@pytest.mark.asyncio
async def test_redis_cache_basic_ops():
    mock_redis = AsyncMock()
    with patch("redis.asyncio.Redis", return_value=mock_redis):
        cache = RedisCache()
        
        # Test client is None branches
        cache.client = None
        assert await cache.get("k") is None
        assert await cache.set("k", "v") is False
        assert await cache.delete("k") is False
        assert await cache.exists("k") is False
        assert await cache.clear() is False
        assert await cache.health_check() is False
        
        # Restore for other tests
        cache.client = mock_redis
        
        # Set (simple)
        mock_redis.set.return_value = True
        assert await cache.set("k1", "v1") is True
        
        # Get (simple)
        data = pickle.dumps("v1")
        mock_redis.get.return_value = data
        assert await cache.get("k1") == "v1"
        
        # Get (None)
        mock_redis.get.return_value = None
        assert await cache.get("empty") is None

        # Delete
        mock_redis.delete.return_value = 1
        assert await cache.delete("k1") is True
        
        # Exists
        mock_redis.exists.return_value = 1
        assert await cache.exists("k1") is True
        
        # Clear
        mock_redis.flushdb.return_value = True
        assert await cache.clear() is True
        
        # Health
        mock_redis.ping.return_value = True
        assert await cache.health_check() is True

        # Test TTL branch (setex)
        mock_redis.setex = AsyncMock(return_value=True)
        assert await cache.set("k_ttl", "v", ttl_seconds=10) is True
        mock_redis.setex.assert_called_once()

@pytest.mark.asyncio
async def test_redis_cache_compression_and_errors():
    mock_redis = AsyncMock()
    with patch("redis.asyncio.Redis", return_value=mock_redis):
        cache = RedisCache(compression_threshold=10)
        large_val = "this is a long string that should be compressed"
        
        await cache.set("large", large_val)
        args, kwargs = mock_redis.set.call_args
        data = args[1]
        assert data.startswith(b"__COMPRESSED__")
        
        # Get should decompress
        mock_redis.get.return_value = data
        assert await cache.get("large") == large_val
        
        # Test Get exception (line 211-213)
        mock_redis.get.side_effect = Exception("failed get")
        assert await cache.get("large") is None
        mock_redis.get.side_effect = None

        # Test Set exception (line 234-236)
        mock_redis.set.side_effect = Exception("failed set")
        assert await cache.set("k", "v") is False
        mock_redis.set.side_effect = None

        # Test Delete exception (line 245-247)
        mock_redis.delete.side_effect = Exception("failed delete")
        assert await cache.delete("k") is False
        mock_redis.delete.side_effect = None

        # Test Exists exception (line 256-258)
        mock_redis.exists.side_effect = Exception("failed exists")
        assert await cache.exists("k") is False
        mock_redis.exists.side_effect = None

        # Test Clear exception (line 268-270)
        mock_redis.flushdb.side_effect = Exception("failed flush")
        assert await cache.clear() is False
        mock_redis.flushdb.side_effect = None

        # Test health_check exception (line 280-281)
        mock_redis.ping.side_effect = Exception("failed ping")
        assert await cache.health_check() is False
        mock_redis.ping.side_effect = None

# ============================================================================
# CacheManager & Decorator Tests
# ============================================================================

@pytest.mark.asyncio
async def test_cache_manager_backend_selection():
    # Force in-memory
    with patch("app.core.cache.redis", None):
        mgr = CacheManager(use_redis=True)
        assert isinstance(mgr.backend, InMemoryCache)

    # Redis healthy
    mock_redis_instance = MagicMock()
    mock_redis_instance._healthy = True
    with patch("app.core.cache.RedisCache", return_value=mock_redis_instance):
        mgr = CacheManager(use_redis=True)
        assert mgr.backend == mock_redis_instance

    # Redis unhealthy (line 313)
    mock_redis_instance._healthy = False
    with patch("app.core.cache.RedisCache", return_value=mock_redis_instance):
        mgr = CacheManager(use_redis=True)
        assert isinstance(mgr.backend, InMemoryCache)

@pytest.mark.asyncio
async def test_cache_manager_generation_keys():
    mgr = CacheManager(use_redis=False)
    
    gen = await mgr.get_generation_key("test")
    assert gen == 0
    
    new_gen = await mgr.increment_generation_key("test")
    assert new_gen == 1
    assert await mgr.get_generation_key("test") == 1

@pytest.mark.asyncio
async def test_cache_manager_redis_generation_incr():
    mock_redis_backend = MagicMock()
    mock_redis_backend.client = AsyncMock()
    mock_redis_backend.client.incr.return_value = 5
    
    mgr = CacheManager(use_redis=False) # initialize with in-memory
    mgr.backend = mock_redis_backend # force redis backend
    
    res = await mgr.increment_generation_key("ns")
    assert res == 5
    mock_redis_backend.client.incr.assert_called_with("generation:ns")

    # Increment failure branch (line 352-353)
    mock_redis_backend.client.incr.side_effect = Exception("incr fail")
    # Should fallback to get/set logic
    with patch.object(mgr, "get_generation_key", return_value=1):
        with patch.object(mgr, "set", return_value=True) as mock_set:
            res = await mgr.increment_generation_key("ns")
            assert res == 2
            mock_set.assert_called_with("generation:ns", 2)
            
@pytest.mark.asyncio
async def test_cache_manager_ops_delegation():
    mgr = CacheManager(use_redis=False)
    mock_backend = AsyncMock()
    mgr.backend = mock_backend
    
    await mgr.get("k")
    mock_backend.get.assert_called_once()
    
    await mgr.set("k", "v")
    mock_backend.set.assert_called_once()
    
    await mgr.delete("k")
    mock_backend.delete.assert_called_once()
    
    await mgr.exists("k")
    mock_backend.exists.assert_called_once()
    
    await mgr.clear()
    mock_backend.clear.assert_called_once()
    
    await mgr.is_healthy()
    mock_backend.health_check.assert_called_once()

@pytest.mark.asyncio
async def test_cache_decorator():
    mgr = CacheManager(use_redis=False)
    decorator = mgr.setup_caching_decorator(ttl_seconds=60)
    
    call_count = 0
    
    @decorator
    async def fast_func(x: int):
        nonlocal call_count
        call_count += 1
        return x * 2

    # First call
    assert await fast_func(5) == 10
    assert call_count == 1
    
    # Second call (hit)
    assert await fast_func(5) == 10
    assert call_count == 1
    
    # Different arg (miss)
    assert await fast_func(6) == 12
    assert call_count == 2

@pytest.mark.asyncio
async def test_cache_decorator_sync_error():
    mgr = CacheManager(use_redis=False)
    decorator = mgr.setup_caching_decorator()
    
    def sync_func():
        return 1
    
    with pytest.raises(TypeError, match="supports async callables only"):
        decorator(sync_func)

def test_get_cache_manager_singleton():
    clear_cache_manager()
    m1 = get_cache_manager(use_redis=False)
    m2 = get_cache_manager()
    assert m1 is m2

def test_redis_import_error_coverage():
    # To cover lines 26-27: except ImportError: pass
    import sys
    with patch.dict("sys.modules", {"redis": None}):
        # Reloading or re-importing in a controlled way is hard, 
        # but we can just trigger the logic if we were to re-run the module code.
        # Since 100% is the goal, we can use a small hack to execute those lines.
        import importlib
        import app.core.cache
        importlib.reload(app.core.cache)
        assert app.core.cache.redis is None
