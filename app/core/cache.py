import json
import logging
from typing import Any, Optional

import redis

from app.core.config import settings


logger = logging.getLogger(__name__)


class CacheService:
    """
    Service for managing Redis-based caching.
    Provides simple get, set, and delete operations with JSON serialization.
    """

    def __init__(self) -> None:
        """
        Initializes the Redis connection pool.
        """
        redis_url = settings.REDIS_URL or f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"
        
        try:
            self.client = redis.from_url(redis_url, decode_responses = True)
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {str(e)}")
            self.client = None

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieves and deserializes data from the cache.
        """
        if not self.client:
            return None
            
        try:
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {str(e)}")
            return None

    def set(self, key: str, value: Any, expire_seconds: int = 3600) -> bool:
        """
        Serializes and stores data in the cache with an expiration time.
        """
        if not self.client:
            return False
            
        try:
            self.client.set(key, json.dumps(value), ex = expire_seconds)
            return True
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """
        Removes a specific key from the cache.
        """
        if not self.client:
            return False
            
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {str(e)}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        Removes all keys matching a specific pattern.
        """
        if not self.client:
            return 0
            
        try:
            keys = self.client.keys(pattern)
            
            if keys:
                return self.client.delete(*keys)
                
            return 0
        except Exception as e:
            logger.error(f"Redis DELETE_PATTERN error for pattern {pattern}: {str(e)}")
            return 0


cache = CacheService()
