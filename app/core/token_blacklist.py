from __future__ import annotations

import logging
import threading
import time
from typing import Dict, Any

from config.settings import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory fallback (also used in tests)
# Maps jti → expiry timestamp (unix float).  Entries are lazily cleaned up.
# ---------------------------------------------------------------------------
_memory_store: Dict[str, float] = {}
_memory_lock = threading.Lock()


def _memory_blacklist(jti: str, ttl_seconds: int) -> None:
    """Store JTI in the in-memory fallback with an expiry timestamp."""
    with _memory_lock:
        _memory_store[jti] = time.time() + ttl_seconds
        # Lazy cleanup: purge expired entries every time we write
        now = time.time()
        expired = [k for k, v in _memory_store.items() if v < now]
        for k in expired:
            del _memory_store[k]


def _memory_is_blacklisted(jti: str) -> bool:
    """Return True if the JTI is present and not yet expired."""
    with _memory_lock:
        expiry = _memory_store.get(jti)
        if expiry is None:
            return False
        if time.time() > expiry:
            del _memory_store[jti]
            return False
        return True


# ---------------------------------------------------------------------------
# Redis helpers
# ---------------------------------------------------------------------------
BLACKLIST_PREFIX = "jti_blacklist:"
_redis_client: Any = None


async def _get_async_redis_client():
    """Return an async Redis client or None if unavailable/disabled."""
    global _redis_client
    if not getattr(settings, "REDIS_ENABLED", False):
        return None
    
    if _redis_client is not None:
        return _redis_client

    try:
        import redis.asyncio as aioredis

        _redis_client = aioredis.Redis(
            host=getattr(settings, "REDIS_HOST", "localhost"),
            port=getattr(settings, "REDIS_PORT", 6379),
            db=1,  # Use db=1 to isolate from rate-limiter keys in db=0
            decode_responses=True,
            socket_connect_timeout=1,
        )
        await _redis_client.ping()
        return _redis_client
    except Exception as exc:
        logger.warning("JTI blacklist: Redis unavailable, using in-memory fallback: %s", exc)
        _redis_client = None
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def blacklist_token(jti: str, ttl_seconds: int) -> None:
    """
    Blacklist a JWT by its JTI claim.

    The entry expires automatically after *ttl_seconds*, which should match
    the token's remaining lifetime so that Redis keys don't accumulate.

    Args:
        jti: The 'jti' claim value extracted from the decoded JWT payload.
        ttl_seconds: Time-to-live in seconds (use token's remaining lifetime).
    """
    if ttl_seconds <= 0:
        return  # Token is already expired — nothing to blacklist

    # In test environments, always use in-memory to avoid Redis dependency
    if settings.APP_ENV == "test":
        _memory_blacklist(jti, ttl_seconds)
        return

    client = await _get_async_redis_client()
    if client:
        try:
            key = f"{BLACKLIST_PREFIX}{jti}"
            await client.setex(key, ttl_seconds, "1")
            logger.debug("JTI blacklisted in Redis: %s (TTL=%ds)", jti, ttl_seconds)
            return
        except Exception as exc:
            logger.warning("JTI blacklist: Redis write failed, falling back to memory: %s", exc)

    _memory_blacklist(jti, ttl_seconds)


async def is_token_blacklisted(jti: str) -> bool:
    """
    Return True if the token has been blacklisted (i.e. revoked).

    Args:
        jti: The 'jti' claim value extracted from the decoded JWT payload.

    Returns:
        bool: True if the token is revoked and should be rejected.
    """
    if settings.APP_ENV == "test":
        return _memory_is_blacklisted(jti)

    client = await _get_async_redis_client()
    if client:
        try:
            key = f"{BLACKLIST_PREFIX}{jti}"
            exists = await client.exists(key)
            return bool(exists)
        except Exception as exc:
            logger.warning("JTI blacklist: Redis read failed, falling back to memory: %s", exc)

    return _memory_is_blacklisted(jti)


def clear_blacklist() -> None:
    """Clear all entries from the in-memory blacklist (used for tests)."""
    with _memory_lock:
        _memory_store.clear()
