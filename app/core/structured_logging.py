"""
Structured logging configuration with correlation IDs and contextualization.

This module provides enhanced logging capabilities for the Bizify API, including:
- JSON structured logging format
- Request correlation IDs for tracing
- Contextualized logging with request metadata
- Performance metrics and timing information
"""

import json
import logging
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
import threading

# Create thread-local storage for correlation IDs
_context = threading.local()


@dataclass
class LogContext:
    """Context information for structured logging."""
    correlation_id: str
    user_id: Optional[str] = None
    request_path: Optional[str] = None
    request_method: Optional[str] = None
    session_id: Optional[str] = None
    service_name: str = "bizify"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class StructuredFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON for structured logging."""
        log_data = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add context if available
        context = get_log_context()
        if context:
            log_data.update(asdict(context))

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add any extra fields
        if hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                if key not in (
                    "name", "msg", "args", "created", "filename", "funcName",
                    "levelname", "levelno", "lineno", "module", "msecs", "message",
                    "pathname", "process", "processName", "relativeCreated", "thread",
                    "threadName", "exc_info", "exc_text", "stack_info"
                ):
                    log_data[key] = value

        return json.dumps(log_data, default=str)


def get_log_context() -> Optional[LogContext]:
    """Get the current log context from thread-local storage."""
    return getattr(_context, "context", None)


def set_log_context(context: LogContext) -> None:
    """Set the log context in thread-local storage."""
    _context.context = context


def clear_log_context() -> None:
    """Clear the log context from thread-local storage."""
    if hasattr(_context, "context"):
        delattr(_context, "context")


@contextmanager
def log_context(
    correlation_id: str,
    user_id: Optional[str] = None,
    request_path: Optional[str] = None,
    request_method: Optional[str] = None,
    session_id: Optional[str] = None,
):
    """
    Context manager for structured logging with correlation ID.
    
    Usage:
        with log_context(correlation_id="abc-123", user_id="user-123"):
            logger.info("Processing request")
    """
    context = LogContext(
        correlation_id=correlation_id,
        user_id=user_id,
        request_path=request_path,
        request_method=request_method,
        session_id=session_id,
    )
    set_log_context(context)
    try:
        yield context
    finally:
        clear_log_context()


class PerformanceTimer:
    """Context manager for timing operations and logging performance."""

    def __init__(
        self,
        logger: logging.Logger,
        operation_name: str,
        threshold_ms: float = 100.0,
        log_level: int = logging.DEBUG,
    ):
        """
        Initialize performance timer.
        
        Args:
            logger: Logger instance to use
            operation_name: Name of the operation being timed
            threshold_ms: Threshold in milliseconds for warning level
            log_level: Logging level (default: DEBUG)
        """
        self.logger = logger
        self.operation_name = operation_name
        self.threshold_ms = threshold_ms
        self.log_level = log_level
        self.start_time: Optional[float] = None
        self.duration_ms: float = 0.0

    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        self.logger.log(
            self.log_level,
            f"Starting operation: {self.operation_name}"
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and log result."""
        self.duration_ms = (time.time() - self.start_time) * 1000
        
        if exc_type is not None:
            self.logger.error(
                f"Operation {self.operation_name} failed after {self.duration_ms:.2f}ms",
                extra={"duration_ms": self.duration_ms, "error": str(exc_val)},
            )
        elif self.duration_ms > self.threshold_ms:
            self.logger.warning(
                f"Operation {self.operation_name} took {self.duration_ms:.2f}ms (threshold: {self.threshold_ms}ms)",
                extra={"duration_ms": self.duration_ms, "slow": True},
            )
        else:
            self.logger.log(
                self.log_level,
                f"Operation {self.operation_name} completed in {self.duration_ms:.2f}ms",
                extra={"duration_ms": self.duration_ms},
            )


def configure_structured_logging(log_level: str = "INFO") -> None:
    """
    Configure structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Create console handler with structured formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)

    # Configure specific loggers
    loggers_config = {
        "bizify": log_level,
        "bizify.api": log_level,
        "bizify.services": log_level,
        "sqlalchemy.engine": "WARNING",
        "sqlalchemy.pool": "WARNING",
        "uvicorn": log_level,
    }

    for logger_name, level in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, level))


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with structured logging.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
