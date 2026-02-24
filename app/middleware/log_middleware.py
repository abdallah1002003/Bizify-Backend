"""
Enhanced logging middleware with structured logging and correlation IDs.

This middleware:
- Generates correlation IDs for request tracing
- Logs structured request/response information
- Tracks performance metrics
- Adds correlation IDs to response headers
"""

import logging
import time
import re
import uuid
from typing import Any, Callable
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
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
        # Generate or retrieve correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        
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

        # Store in request state for access in routes
        request.state.correlation_id = correlation_id
        request.state.request_id = correlation_id  # For backward compatibility

        with log_context(
            correlation_id=correlation_id,
            user_id=user_id,
            request_path=path,
            request_method=request.method,
        ):
            try:
                with PerformanceTimer(logger, f"{request.method} {path}", threshold_ms=500) as timer:
                    response = await call_next(request)

                logger.info(
                    f"Request completed successfully",
                    extra={
                        "status_code": response.status_code,
                        "duration_ms": timer.duration_ms,
                        "path": path,
                        "method": request.method,
                    }
                )

                # Add correlation ID to response headers
                response.headers["X-Correlation-ID"] = correlation_id
                return response

            except Exception as e:
                logger.exception(
                    f"Request processing failed",
                    extra={
                        "path": path,
                        "method": request.method,
                        "error_type": type(e).__name__,
                    }
                )
                raise
