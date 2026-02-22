import asyncio
from collections import defaultdict, deque
import time
from typing import Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from config.settings import settings


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: Optional[int] = None):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute or settings.RATE_LIMIT_PER_MINUTE
        self.window_size = 60  # seconds
        self.request_counts: defaultdict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    def _get_client_ip(self, request: Request) -> str:
        # X-Forwarded-For is forgeable by clients. Rely strictly on client connection IP.
        return request.client.host if request.client else "127.0.0.1"

    async def dispatch(self, request: Request, call_next):
        if settings.APP_ENV == "test":
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        current_time = time.time()

        async with self._lock:
            bucket = self.request_counts[client_ip]
            cutoff = current_time - self.window_size
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) >= self.requests_per_minute:
                retry_after = max(1, int(self.window_size - (current_time - bucket[0])))
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests"},
                    headers={"Retry-After": str(retry_after)},
                )

            bucket.append(current_time)

            # Opportunistic cleanup to avoid unbounded growth.
            stale_ips = [ip for ip, times in self.request_counts.items() if not times]
            for ip in stale_ips:
                self.request_counts.pop(ip, None)

        return await call_next(request)
