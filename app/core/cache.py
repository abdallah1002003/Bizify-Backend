"""
Redis caching service with automatic fallback to in-memory caching.

Features:
- Automatic Redis connection and fallback to in-memory dict
- Configurable TTL per cache key
- Type-safe generic caching
- Performance metrics and logging
- Automatic compression for large values
"""

import json
import pickle
import zlib
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar, Generic, cast
from functools import wraps
from time import time
from app.core.structured_logging import get_logger, PerformanceTimer
from config.settings import settings

redis: Any = None
try:
    import redis as redis_mod
    redis = redis_mod
except ImportError:
    pass



logger = get_logger(__name__)

T = TypeVar("T")


class CacheBackend(ABC, Generic[T]):
    """Abstract base for cache backends."""

    @abstractmethod
    async def get(self, key: str) -> Optional[T]:
        """Retrieve value from cache."""
        pass

    @abstractmethod
    async def set(self, key: str, value: T, ttl_seconds: Optional[int] = None) -> bool:
        """Store value in cache with optional TTL."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache entries."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check backend health."""
        pass


class InMemoryCache(CacheBackend[T]):
    """
    Simple in-memory cache implementation.
    
    Used as fallback when Redis is unavailable. Not suitable for
    production with multiple workers.
    """

    def __init__(self):
        """Initialize in-memory cache."""
        self._cache: Dict[str, tuple[Any, Optional[float]]] = {}
        self._hits = 0
        self._misses = 0

    async def get(self, key: str) -> Optional[T]:
        """
        Retrieve value from in-memory cache.
        
        Returns None if key is missing or expired.
        """
        if key not in self._cache:
            self._misses += 1
            return None

        value, expiration = self._cache[key]
        if expiration is not None and time() > expiration:
            del self._cache[key]
            self._misses += 1
            return None

        self._hits += 1
        return cast(T, value)

    async def set(self, key: str, value: T, ttl_seconds: Optional[int] = None) -> bool:
        """Store value with optional TTL."""
        expiration = None
        if ttl_seconds is not None:
            expiration = time() + ttl_seconds

        self._cache[key] = (value, expiration)
        return True

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    async def exists(self, key: str) -> bool:
        """Check if key exists and hasn't expired."""
        if key not in self._cache:
            return False

        value, expiration = self._cache[key]
        if expiration is not None and time() > expiration:
            del self._cache[key]
            return False

        return True

    async def clear(self) -> bool:
        """Clear all cache entries."""
        self._cache.clear()
        return True

    async def health_check(self) -> bool:
        """In-memory cache is always healthy."""
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "size": len(self._cache),
        }


class RedisCache(CacheBackend[T]):
    """
    Redis-based cache implementation with compression support.
    
    Automatically compresses values larger than threshold to save memory.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        password: Optional[str] = None,
        db: int = 0,
        compression_threshold: int = 1024,  # Compress if > 1KB
    ):
        """
        Initialize Redis cache.
        """
        from redis.asyncio import Redis
        self.compression_threshold = compression_threshold
        self._healthy = False
        self.client: Optional[Redis] = None

        try:
            self.client = Redis(
                host=host,
                port=port,
                password=password,
                db=db,
                decode_responses=False,  # Handle bytes manually
                socket_connect_timeout=2,
                socket_keepalive=True,
            )
            # Ping is async now, so we can't easily wait in __init__
            # We'll trust the configuration and handle health errors in methods
            self._healthy = True
            logger.info(f"Redis client initialized: {host}:{port}")
        except Exception as e:
            logger.warning(f"Redis initialization failed: {e}. Using in-memory fallback.")
            self.client = None
            self._healthy = False

    async def get(self, key: str) -> Optional[T]:
        """Retrieve value from Redis."""
        if not self.client:
            return None

        try:
            # Check health lazily if needed, but usually just catch the exception
            with PerformanceTimer(logger, f"redis.get({key})", threshold_ms=50):
                data = await self.client.get(key)

            if data is None:
                return None

            # Check if compressed
            if data.startswith(b"__COMPRESSED__"):
                data = zlib.decompress(data[14:])  # Skip marker
            return cast(T, pickle.loads(data))
        except Exception as e:
            logger.error(f"Redis get failed for {key}: {e}")
            return None

    async def set(self, key: str, value: T, ttl_seconds: Optional[int] = None) -> bool:
        """Store value in Redis with optional TTL."""
        if not self.client:
            return False

        try:
            with PerformanceTimer(logger, f"redis.set({key})", threshold_ms=50):
                data = pickle.dumps(value)

                # Compress if larger than threshold
                if len(data) > self.compression_threshold:
                    data = b"__COMPRESSED__" + zlib.compress(data)

                if ttl_seconds:
                    await self.client.setex(key, ttl_seconds, data)
                else:
                    await self.client.set(key, data)

            return True
        except Exception as e:
            logger.error(f"Redis set failed for {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        if not self.client:
            return False

        try:
            return bool(await self.client.delete(key))
        except Exception as e:
            logger.error(f"Redis delete failed for {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        if not self.client:
            return False

        try:
            return bool(await self.client.exists(key))
        except Exception as e:
            logger.error(f"Redis exists check failed for {key}: {e}")
            return False

    async def clear(self) -> bool:
        """Clear all keys in current database."""
        if not self.client:
            return False

        try:
            await self.client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Redis clear failed: {e}")
            return False

    async def health_check(self) -> bool:
        """Check Redis connection health."""
        if not self.client:
            return False

        try:
            await self.client.ping()
            return True
        except Exception:
            return False


class CacheManager:
    """
    High-level cache manager with automatic backend selection.
    
    Attempts to use Redis, falls back to in-memory cache if unavailable.
    """

    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_password: Optional[str] = None,
        use_redis: bool = True,
    ):
        """
        Initialize cache manager.
        """
        self.backend: CacheBackend = InMemoryCache()

        if use_redis and redis is not None:
            redis_backend: RedisCache = RedisCache(
                host=redis_host,
                port=redis_port,
                password=redis_password,
            )
            if redis_backend._healthy:
                self.backend = redis_backend
                logger.info("Cache manager initialized with Redis backend")
            else:
                logger.info("Cache manager initialized with in-memory fallback due to Redis failure")
        else:
            logger.info("Cache manager initialized with in-memory backend")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        return await self.backend.get(key)

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Set value in cache."""
        return await self.backend.set(key, value, ttl_seconds)

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        return await self.backend.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        return await self.backend.exists(key)

    async def clear(self) -> bool:
        """Clear cache."""
        return await self.backend.clear()

    async def get_generation_key(self, namespace: str) -> int:
        """Get the current generation (version) for a namespace."""
        gen = await self.get(f"generation:{namespace}")
        if gen is None:
            gen = 0
            await self.set(f"generation:{namespace}", gen)
        return int(gen)

    async def increment_generation_key(self, namespace: str) -> int:
        """Increment the generation for a namespace to invalidate all associated cached items."""
        if hasattr(self.backend, "client") and self.backend.client:
            # Atomic increment in Redis
            try:
                new_gen = await self.backend.client.incr(f"generation:{namespace}")
                return int(new_gen)
            except Exception:
                pass
        
        # Fallback for in-memory or error
        gen = await self.get_generation_key(namespace)
        new_gen = gen + 1
        await self.set(f"generation:{namespace}", new_gen)
        return int(new_gen)

    async def is_healthy(self) -> bool:
        """Check backend health."""
        return await self.backend.health_check()

    def setup_caching_decorator(self, ttl_seconds: int = 3600):
        """
        Create an async-only caching decorator.
        """
        import inspect

        def decorator(func: Any) -> Any:
            if not inspect.iscoroutinefunction(func):
                raise TypeError(
                    "setup_caching_decorator supports async callables only"
                )

            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                cache_key = f"{func.__name__}:{json.dumps([str(arg) for arg in args] + [f'{k}={v}' for k, v in kwargs.items()], sort_keys=True, default=str)}"
                cached = await self.get(cache_key)
                if cached is not None:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached
                result = await func(*args, **kwargs)
                await self.set(cache_key, result, ttl_seconds)
                return result

            return async_wrapper

        return decorator


# Global cache manager instance (initialized lazily)
_cache_manager: Optional[CacheManager] = None


def get_cache_manager(
    redis_host: Optional[str] = None,
    redis_port: Optional[int] = None,
    redis_password: Optional[str] = None,
    use_redis: Optional[bool] = None,
) -> CacheManager:
    """
    Get or create the global cache manager.
    
    Args:
        redis_host: Redis host
        redis_port: Redis port
        redis_password: Redis password
        use_redis: Enable Redis (default: True)
    
    Returns:
        CacheManager instance
    """
    global _cache_manager
    
    # Dynamically inject settings at runtime instead of module parse time
    if redis_host is None:
        redis_host = settings.REDIS_HOST
    if redis_port is None:
        redis_port = settings.REDIS_PORT
    if redis_password is None:
        redis_password = settings.REDIS_PASSWORD
    if use_redis is None:
        use_redis = settings.REDIS_ENABLED

    if _cache_manager is None:
        _cache_manager = CacheManager(
            redis_host=redis_host,
            redis_port=redis_port,
            redis_password=redis_password,
            use_redis=use_redis,
        )
    return _cache_manager


def clear_cache_manager() -> None:
    """Clear the global cache manager (mainly for testing)."""
    global _cache_manager
    _cache_manager = None
