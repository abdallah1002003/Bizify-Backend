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
import logging
import pickle
import zlib
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, TypeVar, Generic
from functools import wraps
from time import time

try:
    import redis
except ImportError:
    redis = None  # type: ignore

from app.core.structured_logging import get_logger, PerformanceTimer

logger = get_logger(__name__)

T = TypeVar("T")


class CacheBackend(ABC, Generic[T]):
    """Abstract base for cache backends."""

    @abstractmethod
    def get(self, key: str) -> Optional[T]:
        """Retrieve value from cache."""
        pass

    @abstractmethod
    def set(self, key: str, value: T, ttl_seconds: Optional[int] = None) -> bool:
        """Store value in cache with optional TTL."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass

    @abstractmethod
    def clear(self) -> bool:
        """Clear all cache entries."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
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

    def get(self, key: str) -> Optional[T]:
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
        return value

    def set(self, key: str, value: T, ttl_seconds: Optional[int] = None) -> bool:
        """Store value with optional TTL."""
        expiration = None
        if ttl_seconds is not None:
            expiration = time() + ttl_seconds

        self._cache[key] = (value, expiration)
        return True

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def exists(self, key: str) -> bool:
        """Check if key exists and hasn't expired."""
        if key not in self._cache:
            return False

        value, expiration = self._cache[key]
        if expiration is not None and time() > expiration:
            del self._cache[key]
            return False

        return True

    def clear(self) -> bool:
        """Clear all cache entries."""
        self._cache.clear()
        return True

    def health_check(self) -> bool:
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
        
        Args:
            host: Redis host (default: localhost)
            port: Redis port (default: 6379)
            password: Redis password (optional)
            db: Database number (default: 0)
            compression_threshold: Size threshold for compression (bytes)
        """
        self.compression_threshold = compression_threshold
        self._healthy = False

        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                password=password,
                db=db,
                decode_responses=False,  # Handle bytes manually
                socket_connect_timeout=2,
                socket_keepalive=True,
            )
            # Test connection
            self.client.ping()
            self._healthy = True
            logger.info(f"Redis connected: {host}:{port}")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using in-memory fallback.")
            self.client = None  # type: ignore
            self._healthy = False

    def get(self, key: str) -> Optional[T]:
        """Retrieve value from Redis."""
        if not self.client:
            return None

        try:
            with PerformanceTimer(logger, f"redis.get({key})", threshold_ms=50):
                data = self.client.get(key)

            if data is None:
                return None

            # Check if compressed
            if data.startswith(b"__COMPRESSED__"):
                data = zlib.decompress(data[14:])  # Skip marker
            return pickle.loads(data)
        except Exception as e:
            logger.error(f"Redis get failed for {key}: {e}")
            return None

    def set(self, key: str, value: T, ttl_seconds: Optional[int] = None) -> bool:
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
                    self.client.setex(key, ttl_seconds, data)
                else:
                    self.client.set(key, data)

            return True
        except Exception as e:
            logger.error(f"Redis set failed for {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        if not self.client:
            return False

        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Redis delete failed for {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        if not self.client:
            return False

        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Redis exists check failed for {key}: {e}")
            return False

    def clear(self) -> bool:
        """Clear all keys in current database."""
        if not self.client:
            return False

        try:
            self.client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Redis clear failed: {e}")
            return False

    def health_check(self) -> bool:
        """Check Redis connection health."""
        if not self.client:
            return False

        try:
            self.client.ping()
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
        
        Args:
            redis_host: Redis host
            redis_port: Redis port
            redis_password: Redis password (optional)
            use_redis: Try to use Redis (default: True)
        """
        self.backend: CacheBackend = InMemoryCache()

        if use_redis and redis is not None:
            redis_cache = RedisCache(
                host=redis_host,
                port=redis_port,
                password=redis_password,
            )
            if redis_cache.health_check():
                self.backend = redis_cache
                logger.info("Cache manager using Redis backend")
            else:
                logger.warning("Cache manager using in-memory fallback")
        else:
            logger.info("Cache manager using in-memory backend")

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        return self.backend.get(key)

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Set value in cache."""
        return self.backend.set(key, value, ttl_seconds)

    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        return self.backend.delete(key)

    def exists(self, key: str) -> bool:
        """Check if key exists."""
        return self.backend.exists(key)

    def clear(self) -> bool:
        """Clear cache."""
        return self.backend.clear()

    def get_generation_key(self, namespace: str) -> int:
        """Get the current generation (version) for a namespace."""
        gen = self.get(f"generation:{namespace}")
        if gen is None:
            gen = 0
            self.set(f"generation:{namespace}", gen)
        return gen

    def increment_generation_key(self, namespace: str) -> int:
        """Increment the generation for a namespace to invalidate all associated cached items."""
        if hasattr(self.backend, "client") and self.backend.client:
            # Atomic increment in Redis
            try:
                new_gen = self.backend.client.incr(f"generation:{namespace}")
                return int(new_gen)
            except Exception:
                pass
        
        # Fallback for in-memory or error
        gen = self.get_generation_key(namespace)
        new_gen = gen + 1
        self.set(f"generation:{namespace}", new_gen)
        return new_gen

    def is_healthy(self) -> bool:
        """Check backend health."""
        return self.backend.health_check()

    def setup_caching_decorator(self, ttl_seconds: int = 3600):
        """
        Create a caching decorator for synchronous functions.
        
        Example:
            @cache_manager.setup_caching_decorator(ttl_seconds=300)
            def get_user_profile(user_id: UUID):
                # Expensive operation
                pass
        """
        def decorator(func):
            import inspect
            
            if inspect.iscoroutinefunction(func):
                @wraps(func)
                async def async_wrapper(*args, **kwargs):
                    cache_key = f"{func.__name__}:{json.dumps([str(arg) for arg in args] + [f'{k}={v}' for k, v in kwargs.items()], sort_keys=True, default=str)}"
                    cached = self.get(cache_key)
                    if cached is not None:
                        logger.debug(f"Cache hit for {func.__name__}")
                        return cached
                    result = await func(*args, **kwargs)
                    self.set(cache_key, result, ttl_seconds)
                    return result
                return async_wrapper
            else:
                @wraps(func)
                def sync_wrapper(*args, **kwargs):
                    cache_key = f"{func.__name__}:{json.dumps([str(arg) for arg in args] + [f'{k}={v}' for k, v in kwargs.items()], sort_keys=True, default=str)}"
                    cached = self.get(cache_key)
                    if cached is not None:
                        logger.debug(f"Cache hit for {func.__name__}")
                        return cached
                    result = func(*args, **kwargs)
                    self.set(cache_key, result, ttl_seconds)
                    return result
                return sync_wrapper

        return decorator


# Global cache manager instance (initialized lazily)
_cache_manager: Optional[CacheManager] = None


def get_cache_manager(
    redis_host: str = "localhost",
    redis_port: int = 6379,
    redis_password: Optional[str] = None,
    use_redis: bool = True,
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
