# type: ignore
import asyncio
from collections import defaultdict, deque
import time
from typing import Optional, Dict, Any, Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from config.settings import settings
import jwt

# Paths with stricter rate limit requirements
STRICT_RATE_LIMIT_PATHS: Dict[str, int] = {
    "/api/v1/auth/login": 5,  # 5 login attempts per minute max
    "/api/v1/auth/bootstrap-admin": 3,  # 3 bootstrap attempts per minute max
}


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    WARNING: This is an in-memory rate limiter, suitable for a single-instance deployment.
    When scaling this application horizontally (multiple workers/instances), this rate limiter 
    will not share state across instances, allowing users to exceed the global rate limit.

    For production at scale, replace this with a Redis-based rate limiter.
    Example implementation snippet using Redis:

    ```python
    import redis.asyncio as redis
    from config.settings import settings

    redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)

    async def check_rate_limit(redis_client, client_ip: str, limit: int, window: int):
        pipe = redis_client.pipeline()
        now = time.time()
        pipe.zremrangebyscore(client_ip, 0, now - window)
        pipe.zadd(client_ip, {str(now): now})
        pipe.zcard(client_ip)
        pipe.expire(client_ip, window)
        _, _, count, _ = await pipe.execute()
        return count <= limit
    ```
    """
    def __init__(self, app: Any, requests_per_minute: Optional[int] = None):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute or settings.RATE_LIMIT_PER_MINUTE
        self.window_size = 60  # seconds
        self.request_counts: defaultdict[str, deque[float]] = defaultdict(deque)
        self._locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    def _get_client_ip(self, request: Request) -> str:
        # X-Forwarded-For is forgeable by clients. Rely strictly on client connection IP.
        return request.client.host if request.client else "127.0.0.1"

    async def dispatch(self, request: Request, call_next: Callable[..., Any]) -> Any:
        if settings.APP_ENV == "test":
            return await call_next(request)

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

        current_time = time.time()
        
        # Check if this path has a stricter limit
        limit = STRICT_RATE_LIMIT_PATHS.get(request.url.path, self.requests_per_minute)

        async with self._locks[rate_key]:
            bucket = self.request_counts[rate_key]
            cutoff = current_time - self.window_size
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) >= limit:
                retry_after = max(1, int(self.window_size - (current_time - bucket[0])))
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests"},
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Window": str(self.window_size),
                    },
                )

            bucket.append(current_time)
            remaining = limit - len(bucket)

            # Opportunistic cleanup to avoid unbounded growth.
            stale_ips = [ip for ip, times in self.request_counts.items() if not times]
            for ip in stale_ips:
                self.request_counts.pop(ip, None)
                self._locks.pop(ip, None)

            stale_locks = [ip for ip in self._locks.keys() if ip not in self.request_counts or not self.request_counts[ip]]
            for ip in stale_locks:
                self._locks.pop(ip, None)

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(self.window_size)
        return response
