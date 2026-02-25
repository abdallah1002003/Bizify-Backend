"""
Redis-backed rate limiter middleware for distributed deployments.

This is a production-ready rate limiter suitable for horizontal scaling with multiple workers/instances.
It uses Redis to maintain shared state across all instances.

Configuration:
- Set REDIS_ENABLED=true in .env to enable Redis
- Set REDIS_HOST, REDIS_PORT in .env
- Falls back to in-memory if Redis is unavailable
"""

import asyncio
import time
from typing import Optional, Dict, List, Any, Callable
import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from config.settings import settings
import jwt

logger = logging.getLogger(__name__)
# Paths with stricter rate limit requirements
STRICT_RATE_LIMIT_PATHS = {
    "/api/v1/auth/login": 5,  # 5 login attempts per minute max
    "/api/v1/auth/bootstrap-admin": 3,  # 3 bootstrap attempts per minute max
}


class RedisRateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Rate limiter using Redis as backend.
    
    Provides distributed rate limiting across multiple instances.
    Falls back to in-memory limiting if Redis is unavailable.
    """
    
    def __init__(self, app: Any, requests_per_minute: Optional[int] = None):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute or settings.RATE_LIMIT_PER_MINUTE
        self.window_size = 60  # seconds
        self.redis_client: Any = None
        self.fallback_in_memory: Dict[str, List[float]] = {}
        self._lock = asyncio.Lock()
        self._redis_available = False
        
    async def _init_redis(self) -> None:
        """Initialize Redis connection on first request."""
        if self._redis_available or self.redis_client:
            return
            
        try:
            import redis.asyncio as redis
            self.redis_client = redis.Redis(
                host=getattr(settings, 'REDIS_HOST', 'localhost'),
                port=getattr(settings, 'REDIS_PORT', 6379),
                db=0,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_keepalive=True,
            )
            # Test connection
            await self.redis_client.ping()
            self._redis_available = True
            logger.info("Redis rate limiter connected successfully")
        except Exception as e:
            logger.warning(f"Redis rate limiter unavailable, falling back to in-memory: {e}")
            self._redis_available = False
            self.redis_client = None

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        return request.client.host if request.client else "127.0.0.1"

    async def _check_rate_limit_redis(self, client_ip: str, request_path: str) -> tuple[bool, int, int]:
        """Check rate limit using Redis."""
        try:
            key = f"rate_limit:{client_ip}"
            now = time.time()
            pipe = self.redis_client.pipeline()
            
            # Remove old entries outside the window
            pipe.zremrangebyscore(key, 0, now - self.window_size)
            # Add current timestamp
            pipe.zadd(key, {str(now): now})
            # Get count
            pipe.zcard(key)
            # Set expiration
            pipe.expire(key, self.window_size + 1)
            
            results = await pipe.execute()
            count = results[2]  # zcard result
            
            # Check if this path has a stricter limit
            limit = STRICT_RATE_LIMIT_PATHS.get(request_path, self.requests_per_minute)
            
            remaining = max(0, limit - count)
            is_allowed = count <= limit
            
            return is_allowed, remaining, limit
        except Exception as e:
            logger.warning(f"Redis check failed for {client_ip}, falling back to in-memory: {e}")
            self._redis_available = False
            # Check if this path has a stricter limit
            limit = STRICT_RATE_LIMIT_PATHS.get(request_path, self.requests_per_minute)
            is_allowed, rem = await self._check_rate_limit_memory(client_ip, limit)
            return is_allowed, rem, limit

    async def _check_rate_limit_memory(self, client_ip: str, limit: int) -> tuple[bool, int]:
        """Fallback in-memory rate limit check."""
        async with self._lock:
            now = time.time()
            
            if client_ip not in self.fallback_in_memory:
                self.fallback_in_memory[client_ip] = []
            
            requests = self.fallback_in_memory[client_ip]
            cutoff = now - self.window_size
            
            # Remove old requests
            requests[:] = [t for t in requests if t > cutoff]
            
            is_allowed = len(requests) < limit
            remaining = max(0, limit - len(requests))
            
            if is_allowed:
                requests.append(now)
            
            # Cleanup stale entries
            if len(self.fallback_in_memory) > 1000:
                empty_ips = [ip for ip, reqs in self.fallback_in_memory.items() if not reqs]
                for ip in empty_ips:
                    del self.fallback_in_memory[ip]
            
            return is_allowed, remaining

    async def dispatch(self, request: Request, call_next: Callable[..., Any]) -> Any:
        """Process request with rate limiting."""
        if settings.APP_ENV == "test":
            return await call_next(request)

        await self._init_redis()
        
        # 1. Identify rate limit key (User ID or Client IP)
        rate_key = self._get_client_ip(request)
        
        # Try to extract user_id from JWT if Authorization header is present
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                payload = jwt.decode(
                    token,
                    settings.jwt_verify_key,
                    algorithms=[settings.jwt_algorithm]
                )
                user_id = payload.get("sub")
                if user_id:
                    rate_key = f"user:{user_id}"
            except (jwt.PyJWTError, Exception):
                # Fallback to IP if token is invalid or decoding fails
                pass
        
        # Check rate limit
        if self._redis_available and self.redis_client:
            is_allowed, remaining, limit = await self._check_rate_limit_redis(rate_key, request.url.path)
        else:
            # For memory fallback, we need to handle limit manually as in Redis
            limit = STRICT_RATE_LIMIT_PATHS.get(request.url.path, self.requests_per_minute)
            is_allowed, remaining = await self._check_rate_limit_memory(rate_key, limit)
        
        if not is_allowed:
            retry_after = self.window_size
            logger.warning(f"Rate limit exceeded for {rate_key}")
            return JSONResponse(
                status_code=429,
                content={
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": retry_after
                },
                headers={"Retry-After": str(retry_after)},
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(self.window_size)
        
        return response
