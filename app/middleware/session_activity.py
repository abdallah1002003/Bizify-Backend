from __future__ import annotations

import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class SessionActivityMiddleware(BaseHTTPMiddleware):
    """Best-effort hook for session activity tracking.

    The project currently has no persisted session model, so this middleware is
    intentionally a no-op and only logs unexpected failures.
    """

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:  # pragma: no cover
            logging.error("Session activity middleware error: %s", exc)
            raise
