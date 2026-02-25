"""
Enhanced logging middleware with structured logging and correlation IDs.

This middleware:
- Generates correlation IDs for request tracing
- Logs structured request/response information
- Tracks performance metrics
- Adds correlation IDs to response headers
"""

import re
import uuid
from typing import Any, Callable
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from app.core.structured_logging import (
    log_context,
    PerformanceTimer,
    get_logger,
)

logger = get_logger("bizify.api.middleware")


class LogMiddleware(BaseHTTPMiddleware):
    """
    HTTP middleware for structured request/response logging.
    
    Features:
    - Generates and propagates correlation IDs
    - Logs request start and completion
    - Tracks performance metrics
    - Adds X-Request-ID header to response
    """

    async def dispatch(self, request: Request, call_next: Callable[..., Any]) -> Any:
        """
        Process request with structured logging.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/route handler
        
        Returns:
            Response with correlation ID header
        """
        # Resolve request ID: prefer X-Request-ID (industry standard), then
        # X-Correlation-ID (legacy), then generate a fresh UUID.
        request_id: str = (
            request.headers.get("X-Request-ID")
            or request.headers.get("X-Correlation-ID")
            or str(uuid.uuid4())
        )
        # Internal correlation ID — always a UUID we control
        correlation_id: str = request.headers.get("X-Correlation-ID") or request_id

        # Extract user ID if available (from JWT or session)
        user_id = None
        if hasattr(request.state, "user_id"):
            user_id = request.state.user_id

        # Sanitize path for logging (replace UUIDs with <id>)
        path = re.sub(
            r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}',
            '<id>',
            request.url.path
        )

        # Store in request state for access in route handlers
        request.state.request_id = request_id
        request.state.correlation_id = correlation_id

        with log_context(
            correlation_id=correlation_id,
            request_id=request_id,
            user_id=user_id,
            request_path=path,
            request_method=request.method,
        ):
            try:
                with PerformanceTimer(logger, f"{request.method} {path}", threshold_ms=500) as timer:
                    response = await call_next(request)

                logger.info(
                    "Request completed successfully",
                    extra={
                        "status_code": response.status_code,
                        "duration_ms": timer.duration_ms,
                        "path": path,
                        "method": request.method,
                        "request_id": request_id,
                    }
                )

                # Echo both headers so clients can trace their request IDs
                response.headers["X-Request-ID"] = request_id
                response.headers["X-Correlation-ID"] = correlation_id
                return response

            except Exception as e:
                logger.exception(
                    "Request processing failed",
                    extra={
                        "path": path,
                        "method": request.method,
                        "error_type": type(e).__name__,
                    }
                )
                raise
