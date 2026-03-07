import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, Response
from app.middleware.log_middleware import LogMiddleware

@pytest.mark.asyncio
class TestLogMiddleware:
    async def test_x_request_id_from_header(self):
        # Setup middleware
        middleware = LogMiddleware(MagicMock())
        
        # Mock request with X-Request-ID header
        request_id = "test-req-id"
        request = MagicMock(spec=Request)
        request.headers = {"X-Request-ID": request_id}
        request.method = "GET"
        request.url.path = "/test"
        request.state = MagicMock()
        
        # Mock call_next
        response = Response()
        call_next = AsyncMock(return_value=response)
        
        # Patch log_context and PerformanceTimer
        with patch("app.middleware.log_middleware.log_context") as mock_log_context:
            with patch("app.middleware.log_middleware.PerformanceTimer") as mock_timer:
                mock_timer.return_value.__enter__.return_value = MagicMock(duration_ms=10.0)
                
                res = await middleware.dispatch(request, call_next)
                
                # Verify headers in response
                assert res.headers["X-Request-ID"] == request_id
                assert res.headers["X-Correlation-ID"] == request_id
                
                # Verify log_context was called with correct IDs
                mock_log_context.assert_called_once()
                args, kwargs = mock_log_context.call_args
                assert kwargs["request_id"] == request_id
                assert kwargs["correlation_id"] == request_id

    async def test_x_request_id_generated_when_absent(self):
        middleware = LogMiddleware(MagicMock())
        
        request = MagicMock(spec=Request)
        request.headers = {} # No headers
        request.method = "POST"
        request.url.path = "/api/v1/chat"
        request.state = MagicMock()
        
        response = Response()
        call_next = AsyncMock(return_value=response)
        
        with patch("app.middleware.log_middleware.log_context"):
            with patch("app.middleware.log_middleware.PerformanceTimer"):
                res = await middleware.dispatch(request, call_next)
                
                # Should have generated a UUID
                res_req_id = res.headers["X-Request-ID"]
                assert uuid.UUID(res_req_id) # Should be valid UUID
                assert res.headers["X-Correlation-ID"] == res_req_id

    async def test_x_correlation_id_fallback(self):
        middleware = LogMiddleware(MagicMock())
        
        corr_id = "test-corr-id"
        request = MagicMock(spec=Request)
        request.headers = {"X-Correlation-ID": corr_id}
        request.method = "GET"
        request.url.path = "/test"
        request.state = MagicMock()
        
        response = Response()
        call_next = AsyncMock(return_value=response)
        
        with patch("app.middleware.log_middleware.log_context"):
            with patch("app.middleware.log_middleware.PerformanceTimer"):
                res = await middleware.dispatch(request, call_next)
                
                # Should use X-Correlation-ID as request_id if X-Request-ID is missing
                assert res.headers["X-Request-ID"] == corr_id
                assert res.headers["X-Correlation-ID"] == corr_id
