from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging
import traceback
from typing import Any, Dict, Callable

from app.core.exceptions import AppException

logger = logging.getLogger(__name__)


class ErrorResponse:
    """Standardized error response structure."""
    
    def __init__(
        self, 
        status_code: int,
        error_code: str,
        message: str,
        details: Any = None
    ):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details
    
    def to_dict(self) -> Dict[str, Any]:
        response = {
            "status_code": self.status_code,
            "error_code": self.error_code,
            "message": self.message,
        }
        if self.details:
            response["details"] = self.details
        return response


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Enhanced error handler middleware with error classification and observability.

    Catches and classifies different exception types:
    - AppException:     Custom app exceptions (various status codes)
    - ValidationError:  422 (VALIDATION_ERROR)
    - IntegrityError:   409 (CONFLICT)
    - SQLAlchemyError:  500 (DATABASE_ERROR)
    - ValueError:       400 (INVALID_VALUE)
    - PermissionError:  403 (FORBIDDEN)
    - Generic Exception: 500 (INTERNAL_ERROR)
    """

    async def dispatch(self, request: Request, call_next: Callable[..., Any]) -> Any:
        try:
            response = await call_next(request)
            return response

        except AppException as exc:
            """Handle custom application exceptions."""
            log_func = logger.warning if exc.status_code < 500 else logger.error
            log_func(
                f"App exception ({exc.code}) on {request.method} {request.url.path}: {exc.message}",
                extra={"code": exc.code, "details": exc.details}
            )
            error = ErrorResponse(
                status_code=exc.status_code,
                error_code=exc.code,
                message=exc.message,
                details=exc.details if exc.details else None
            )
            return JSONResponse(
                status_code=exc.status_code,
                content=error.to_dict()
            )

        except ValidationError as exc:
            """Handle Pydantic validation errors."""
            logger.warning(
                f"Validation error on {request.method} {request.url.path}",
                extra={"errors": exc.errors()}
            )
            error = ErrorResponse(
                status_code=422,
                error_code="VALIDATION_ERROR",
                message="Request validation failed",
                details=exc.errors()
            )
            return JSONResponse(
                status_code=422,
                content=error.to_dict()
            )

        except IntegrityError as exc:
            """Handle database integrity constraint violations."""
            logger.warning(
                f"Database integrity error on {request.method} {request.url.path}",
                extra={"detail": str(exc.orig)}
            )
            error = ErrorResponse(
                status_code=409,
                error_code="CONFLICT",
                message="Resource conflict (duplicate entry or constraint violation)",
                details=str(exc.orig) if exc.orig else None
            )
            return JSONResponse(
                status_code=409,
                content=error.to_dict()
            )

        except SQLAlchemyError as exc:
            """Handle database errors."""
            logger.error(
                f"Database error on {request.method} {request.url.path}: {exc}",
                extra={"trace": traceback.format_exc()}
            )
            error = ErrorResponse(
                status_code=500,
                error_code="DATABASE_ERROR",
                message="Database operation failed",
                details="An error occurred while processing your request"
            )
            return JSONResponse(
                status_code=500,
                content=error.to_dict()
            )

        except ValueError as exc:
            """Handle value errors (e.g., from business logic)."""
            logger.warning(
                f"Value error on {request.method} {request.url.path}: {exc}"
            )
            error = ErrorResponse(
                status_code=400,
                error_code="INVALID_VALUE",
                message=str(exc)
            )
            return JSONResponse(
                status_code=400,
                content=error.to_dict()
            )

        except PermissionError as exc:
            """Handle authorization / access-control denials."""
            logger.warning(
                f"Permission denied on {request.method} {request.url.path}: {exc}"
            )
            error = ErrorResponse(
                status_code=403,
                error_code="FORBIDDEN",
                message=str(exc) or "You do not have permission to perform this action"
            )
            return JSONResponse(
                status_code=403,
                content=error.to_dict()
            )

        except Exception as exc:
            """Catch-all for unexpected exceptions."""
            logger.error(
                f"Unhandled exception on {request.method} {request.url.path}",
                extra={
                    "exception_type": type(exc).__name__,
                    "trace": traceback.format_exc()
                }
            )
            error = ErrorResponse(
                status_code=500,
                error_code="INTERNAL_ERROR",
                message="An unexpected error occurred"
            )
            return JSONResponse(
                status_code=500,
                content=error.to_dict()
            )
