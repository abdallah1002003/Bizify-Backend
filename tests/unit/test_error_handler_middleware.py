"""
Unit tests for ErrorHandlerMiddleware.

Verifies that each custom exception type is translated to the correct
HTTP status code and error_code without leaking internal details.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.error_handler import ErrorHandlerMiddleware


def _app_raising(exc: Exception) -> FastAPI:
    """Build a minimal FastAPI app that always raises `exc` on GET /."""
    app = FastAPI()
    app.add_middleware(ErrorHandlerMiddleware)

    @app.get("/")
    def route():
        raise exc

    return app


# ---------------------------------------------------------------------------
# PermissionError → 403
# ---------------------------------------------------------------------------

class TestPermissionError:
    def test_permission_error_returns_403(self):
        client = TestClient(_app_raising(PermissionError("Access denied")), raise_server_exceptions=False)
        resp = client.get("/")
        assert resp.status_code == 403
        body = resp.json()
        assert body["error_code"] == "FORBIDDEN"
        assert "permission" in body["message"].lower() or "access" in body["message"].lower()

    def test_permission_error_message_is_surfaced(self):
        client = TestClient(_app_raising(PermissionError("Only admins allowed")), raise_server_exceptions=False)
        resp = client.get("/")
        assert resp.status_code == 403
        assert "admins" in resp.json()["message"].lower()

    def test_permission_error_is_not_500(self):
        """Regression: before this fix PermissionError fell through to the 500 catch-all."""
        client = TestClient(_app_raising(PermissionError("nope")), raise_server_exceptions=False)
        assert client.get("/").status_code != 500


# ---------------------------------------------------------------------------
# Other handlers (smoke tests to ensure nothing regressed)
# ---------------------------------------------------------------------------

class TestOtherHandlers:
    def test_value_error_returns_400(self):
        client = TestClient(_app_raising(ValueError("bad input")), raise_server_exceptions=False)
        resp = client.get("/")
        assert resp.status_code == 400
        assert resp.json()["error_code"] == "INVALID_VALUE"

    def test_generic_exception_returns_500(self):
        client = TestClient(_app_raising(RuntimeError("boom")), raise_server_exceptions=False)
        resp = client.get("/")
        assert resp.status_code == 500
        assert resp.json()["error_code"] == "INTERNAL_ERROR"
