"""
Retry Logic with Exponential Backoff
Provides resilient I/O operations for the autonomous system.
"""

import time
import logging
from typing import Callable, TypeVar, Optional, Type, Tuple
from functools import wraps

from core.exceptions import AutonomousSystemError

logger = logging.getLogger(__name__)

T = TypeVar('T')

def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """
    Decorator for retrying operations with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff calculation
        exceptions: Tuple of exception types to catch and retry
    
    Example:
        @retry_with_backoff(max_attempts=3, base_delay=1.0)
        def risky_operation():
            # Code that might fail
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception: Optional[Exception] = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        logger.error(
                            f"Operation {func.__name__} failed after {max_attempts} attempts",
                            extra={"error": str(e), "attempts": max_attempts}
                        )
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** (attempt - 1)), max_delay)
                    
                    logger.warning(
                        f"Operation {func.__name__} failed (attempt {attempt}/{max_attempts}), "
                        f"retrying in {delay:.2f}s",
                        extra={"error": str(e), "attempt": attempt, "delay": delay}
                    )
                    
                    time.sleep(delay)
            
            # This should never be reached, but for type safety
            if last_exception:
                raise last_exception
            raise AutonomousSystemError("Retry logic error: no exception but no success")
        
        return wrapper
    return decorator

class RetryableOperation:
    """
    Context manager for retryable operations with manual control.
    
    Example:
        with RetryableOperation(max_attempts=3) as retry:
            while retry.should_retry():
                try:
                    # Risky operation
                    result = perform_operation()
                    retry.success()
                    break
                except Exception as e:
                    retry.failed(e)
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.current_attempt = 0
        self.last_exception: Optional[Exception] = None
        self._success = False
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None and not self._success:
            logger.error(
                f"RetryableOperation failed after {self.current_attempt} attempts",
                extra={"error": str(exc_val)}
            )
        return False
    
    def should_retry(self) -> bool:
        """Check if another retry attempt should be made."""
        return self.current_attempt < self.max_attempts and not self._success
    
    def failed(self, exception: Exception) -> None:
        """Mark current attempt as failed."""
        self.current_attempt += 1
        self.last_exception = exception
        
        if self.current_attempt < self.max_attempts:
            delay = min(
                self.base_delay * (self.exponential_base ** (self.current_attempt - 1)),
                self.max_delay
            )
            logger.warning(
                f"Attempt {self.current_attempt}/{self.max_attempts} failed, "
                f"retrying in {delay:.2f}s",
                extra={"error": str(exception), "delay": delay}
            )
            time.sleep(delay)
        else:
            logger.error(
                f"All {self.max_attempts} attempts failed",
                extra={"error": str(exception)}
            )
    
    def success(self) -> None:
        """Mark operation as successful."""
        self._success = True
        if self.current_attempt > 1:
            logger.info(
                f"Operation succeeded after {self.current_attempt} attempts"
            )
