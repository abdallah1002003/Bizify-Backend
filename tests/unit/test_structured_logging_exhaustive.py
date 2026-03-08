import pytest
import logging
import json
import time
from unittest.mock import MagicMock, patch
from app.core.structured_logging import (
    StructuredFormatter,
    LogContext,
    get_log_context,
    set_log_context,
    clear_log_context,
    log_context,
    PerformanceTimer,
    configure_structured_logging,
    get_logger,
)

def test_structured_formatter_basic():
    formatter = StructuredFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="test message",
        args=(),
        exc_info=None
    )
    
    formatted = formatter.format(record)
    data = json.loads(formatted)
    
    assert data["message"] == "test message"
    assert data["level"] == "INFO"
    assert data["logger"] == "test_logger"
    assert "timestamp" in data

def test_structured_formatter_with_context():
    formatter = StructuredFormatter()
    context = LogContext(correlation_id="abc-123", user_id="user-1")
    set_log_context(context)
    
    try:
        record = logging.LogRecord("name", logging.INFO, "path", 10, "msg", (), None)
        formatted = formatter.format(record)
        data = json.loads(formatted)
        
        assert data["correlation_id"] == "abc-123"
        assert data["user_id"] == "user-1"
        assert data["service_name"] == "bizify"
    finally:
        clear_log_context()

def test_structured_formatter_with_exception():
    formatter = StructuredFormatter()
    try:
        raise ValueError("boom")
    except ValueError:
        import sys
        exc_info = sys.exc_info()
        
    record = logging.LogRecord("name", logging.ERROR, "path", 10, "msg", (), exc_info)
    formatted = formatter.format(record)
    data = json.loads(formatted)
    
    assert "exception" in data
    assert "ValueError: boom" in data["exception"]

def test_structured_formatter_extra_fields():
    formatter = StructuredFormatter()
    record = logging.LogRecord("name", logging.INFO, "path", 10, "msg", (), None)
    record.custom_field = "custom_value"
    
    formatted = formatter.format(record)
    data = json.loads(formatted)
    assert data["custom_field"] == "custom_value"

def test_log_context_manager():
    clear_log_context()
    assert get_log_context() is None
    
    with log_context(correlation_id="c1", request_id="r1", user_id="u1") as ctx:
        assert get_log_context() == ctx
        assert ctx.correlation_id == "c1"
        assert ctx.request_id == "r1"
    
    assert get_log_context() is None

def test_clear_log_context_missing():
    # Cover lines 84-85 (hasattr checkout)
    clear_log_context() # already cleared
    clear_log_context() # should not raise

def test_performance_timer_success():
    mock_logger = MagicMock()
    with PerformanceTimer(mock_logger, "op1", threshold_ms=50):
        pass # fast
    
    # Verify debug log
    mock_logger.log.assert_called()
    # Check that it didn't log warning/error
    assert mock_logger.warning.called is False
    assert mock_logger.error.called is False

def test_performance_timer_slow():
    mock_logger = MagicMock()
    with PerformanceTimer(mock_logger, "slow_op", threshold_ms=10):
        time.sleep(0.02)
        
    mock_logger.warning.assert_called()
    args, kwargs = mock_logger.warning.call_args
    assert "took" in args[0]
    assert kwargs["extra"]["slow"] is True

def test_performance_timer_failure():
    mock_logger = MagicMock()
    with pytest.raises(ValueError):
        with PerformanceTimer(mock_logger, "failing_op"):
            raise ValueError("failed!")
            
    mock_logger.error.assert_called()
    args, kwargs = mock_logger.error.call_args
    assert "failed after" in args[0]
    assert kwargs["extra"]["error"] == "failed!"

def test_configure_structured_logging():
    with patch("logging.getLogger") as mock_get_logger:
        root = MagicMock()
        mock_get_logger.return_value = root
        
        configure_structured_logging(log_level="DEBUG")
        
        # Verify root logger configuration
        root.setLevel.assert_any_call(logging.DEBUG)
        root.handlers.clear.assert_called()
        root.addHandler.assert_called()

def test_get_logger_helper():
    logger = get_logger("my_logger")
    assert logger.name == "my_logger"
    assert isinstance(logger, logging.Logger)
