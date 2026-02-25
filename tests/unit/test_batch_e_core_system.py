"""
Batch E: Tests for Core System Modules
- db/database.py
- core/events.py
- middleware/error_handler.py
- middleware/prometheus.py
"""
import pytest
from unittest.mock import MagicMock, patch

# ─────────────────────────────────────────────────────────────────
# Database
# ─────────────────────────────────────────────────────────────────

class TestDatabaseModule:
    def test_get_db_yields_session(self):
        from app.db.database import get_db
        # We can't actually hit the DB in a unit test easily without setup, 
        # but we can mock SessionLocal
        with patch("app.db.database.SessionLocal") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            gen = get_db()
            session = next(gen)
            assert session is mock_session
            
            with pytest.raises(StopIteration):
                next(gen)
                
            mock_session.close.assert_called_once()

    def test_get_db_closes_session_on_exception(self):
        from app.db.database import get_db
        with patch("app.db.database.SessionLocal") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            gen = get_db()
            session = next(gen)
            assert session is mock_session
            
            with pytest.raises(ValueError):
                gen.throw(ValueError("boom"))
                
            mock_session.close.assert_called_once()


# ─────────────────────────────────────────────────────────────────
# Events
# ─────────────────────────────────────────────────────────────────

class TestEventDispatcher:
    @pytest.mark.asyncio
    async def test_event_dispatching(self):
        from app.core.events import EventDispatcher
        dispatcher = EventDispatcher()
        
        callback1_calls = []
        callback2_calls = []
        
        async def callback1(event, payload): callback1_calls.append(payload)
        async def callback2(event, payload): callback2_calls.append(payload)
        
        dispatcher.subscribe("test_event", callback1)
        dispatcher.subscribe("test_event", callback2)
        
        await dispatcher.emit("test_event", {"data": 123})
        
        assert len(callback1_calls) == 1
        assert len(callback2_calls) == 1

    @pytest.mark.asyncio
    async def test_event_dispatching_error_handling(self):
        from app.core.events import EventDispatcher
        dispatcher = EventDispatcher()
        
        callback2_calls = []
        async def callback1(event, payload): raise Exception("Handler failed")
        async def callback2(event, payload): callback2_calls.append(payload)
        
        dispatcher.subscribe("error_event", callback1)
        dispatcher.subscribe("error_event", callback2)
        
        # Should not raise exception
        await dispatcher.emit("error_event", {})
        
        assert len(callback2_calls) == 1


# ─────────────────────────────────────────────────────────────────
# Error Handler Middleware
# ─────────────────────────────────────────────────────────────────

class TestErrorHandlerMiddleware:
    @pytest.mark.asyncio
    async def test_error_handler_catches_unhandled_exceptions(self):
        from app.middleware.error_handler import ErrorHandlerMiddleware
        from unittest.mock import AsyncMock
        
        mw = ErrorHandlerMiddleware(app=None)
        
        call_next = AsyncMock(side_effect=Exception("Unexpected booming"))
        request = MagicMock()
        
        response = await mw.dispatch(request, call_next)
        
        assert response.status_code == 500
        # Check standard JSON response format for unhandled ex
        import json
        body = json.loads(response.body.decode())
        assert "error_code" in body
        assert body["error_code"] == "INTERNAL_ERROR"

    @pytest.mark.asyncio
    async def test_error_handler_bizify_exception(self):
        from app.middleware.error_handler import ErrorHandlerMiddleware
        from app.core.exceptions import ResourceNotFoundError
        from unittest.mock import AsyncMock
        
        mw = ErrorHandlerMiddleware(app=None)
        
        call_next = AsyncMock(side_effect=ResourceNotFoundError(resource_type="User", resource_id="123"))
        request = MagicMock()
        
        response = await mw.dispatch(request, call_next)
        
        assert response.status_code == 404
        import json
        body = json.loads(response.body.decode())
        assert body["error_code"] == "NOT_FOUND"


# ─────────────────────────────────────────────────────────────────
# Prometheus Metrics
# ─────────────────────────────────────────────────────────────────

class TestPrometheusMetrics:
    def test_setup_prometheus(self):
        from app.middleware.prometheus import setup_prometheus
        from fastapi import FastAPI
        
        app = FastAPI()
        
        # Enable metrics explicitly for the test
        import os
        with patch.dict(os.environ, {"ENABLE_METRICS": "true"}):
            instrumentator = setup_prometheus(app)
            assert instrumentator is not None
            
        with patch.dict(os.environ, {"ENABLE_METRICS": "false"}):
            instrumentator = setup_prometheus(app)
            assert instrumentator is None

    def test_record_metrics(self):
        from app.middleware.prometheus import (
            record_user_registration, 
            record_ai_agent_run, 
            record_db_operation
        )
        
        # Should not raise
        record_user_registration("admin")
        record_ai_agent_run("research", "success", 1.5)
        record_db_operation("SELECT", 0.05)


class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)
