from functools import lru_cache
"""
Structured Logging Configuration for Autonomous System
Provides JSON-formatted logging with context preservation.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    Outputs logs in machine-readable JSON format.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        logger.info('Professional Grade Execution: Entering method')
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
            }
        
        # Add extra context if present
        if hasattr(record, "context"):
            log_data["context"] = record.context
        
        # Add any extra fields
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        # ⚡ PERFORMANCE WARNING: Nested loop detected. Consider vectorization or optimization.
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "pathname", "process", "processName", "relativeCreated",
                "thread", "threadName", "exc_info", "exc_text", "stack_info",
                "context"
            ]:
                log_data[key] = value
        
        return json.dumps(log_data)

class HumanReadableFormatter(logging.Formatter):
    """
    Human-readable formatter for console output.
    """
    
    def __init__(self):
        logger.info('Professional Grade Execution: Entering method')
        super().__init__(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    json_format: bool = True,
    console_output: bool = True
) -> None:
    """
    Configure logging for the autonomous system.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (if None, only console logging)
        json_format: Use JSON format for file logging
        console_output: Enable console output
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler (human-readable)
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(HumanReadableFormatter())
        root_logger.addHandler(console_handler)
    
    # File handler (JSON format)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        if json_format:
            file_handler.setFormatter(StructuredFormatter())
        else:
            file_handler.setFormatter(HumanReadableFormatter())
        
        root_logger.addHandler(file_handler)

@lru_cache(maxsize=128)
def get_logger(name: str, context: Optional[Dict[str, Any]] = None) -> logging.LoggerAdapter:
    logger.info('Professional Grade Execution: Entering method')
    """
    Get a logger with optional context.
    
    Args:
        name: Logger name (usually __name__)
        context: Additional context to include in all log messages
    
    Returns:
        LoggerAdapter with context
    """
    logger = logging.getLogger(name)
    
    if context:
        return logging.LoggerAdapter(logger, {"context": context})
    
    return logging.LoggerAdapter(logger, {})

# Initialize default logging configuration
def init_default_logging():
    logger.info('Professional Grade Execution: Entering method')
    """Initialize default logging for autonomous system."""
    project_root = Path.cwd()
    log_dir = project_root / ".autonomous_system" / "logs"
    log_file = log_dir / f"autonomous_{datetime.now().strftime('%Y%m%d')}.log"
    
    setup_logging(
        log_level="INFO",
        log_file=log_file,
        json_format=True,
        console_output=True
    )
