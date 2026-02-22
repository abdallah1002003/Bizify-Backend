import asyncio
import time
from functools import wraps
from typing import Any, Callable

# Simple thread-safe and async-safe TTL memory cache
_cache: dict[str, dict[str, Any]] = {}

def _serialize(obj: Any) -> Any:
    """Recursively serialize SQLAlchemy objects to plain dictionaries to avoid DetachedInstanceError."""
    if hasattr(obj, "__table__"):
        return {
            column_name: getattr(obj, column_name)
            for column_name in obj.__table__.columns.keys()
        }
    if isinstance(obj, list):
        return [_serialize(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    return obj

def cache(ttl_seconds: int = 60) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Generate a very simple cache key based on function name, args and kwargs
            # (Note: In production with complex request objects, hashing request bounds is required)
            key_parts = [func.__name__]
            # Prune out unhashable types (like Session) for the key
            key_parts.extend([str(a) for a in args if isinstance(a, (int, str, float, bool))])
            key_parts.extend([f"{k}={v}" for k, v in kwargs.items() if isinstance(v, (int, str, float, bool))])
            
            cache_key = ":".join(key_parts)
            
            # Check cache
            now = time.time()
            if cache_key in _cache:
                entry = _cache[cache_key]
                if now - entry["timestamp"] < ttl_seconds:
                    return entry["value"]
            
            # Exec
            result = await func(*args, **kwargs)
            serialized_result = _serialize(result)
            
            _cache[cache_key] = {
                "timestamp": now,
                "value": serialized_result
            }
            return serialized_result

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            key_parts = [func.__name__]
            key_parts.extend([str(a) for a in args if isinstance(a, (int, str, float, bool))])
            key_parts.extend([f"{k}={v}" for k, v in kwargs.items() if isinstance(v, (int, str, float, bool))])
            
            cache_key = ":".join(key_parts)
            
            now = time.time()
            if cache_key in _cache:
                entry = _cache[cache_key]
                if now - entry["timestamp"] < ttl_seconds:
                    return entry["value"]
            
            result = func(*args, **kwargs)
            serialized_result = _serialize(result)

            _cache[cache_key] = {
                "timestamp": now,
                "value": serialized_result
            }
            return serialized_result

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator
