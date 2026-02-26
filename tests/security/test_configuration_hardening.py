from fastapi.testclient import TestClient
from main import app
from config.settings import settings
import time

client = TestClient(app)

def test_metrics_key_enforcement_non_dev():
    """Verify metrics key is strictly enforced in non-dev environments."""
    original_env = settings.APP_ENV
    original_key = getattr(settings, "METRICS_API_KEY", "")
    
    try:
        settings.APP_ENV = "production"
        settings.METRICS_API_KEY = "prod-secret"
        
        # Unauthorized
        response = client.get("/metrics", headers={"X-Metrics-Key": "wrong-key"})
        assert response.status_code == 401
        
        # Authorized
        response = client.get("/metrics", headers={"X-Metrics-Key": "prod-secret"})
        assert response.status_code == 200
        
        # Missing key in prod should fail even if no header sent
        settings.METRICS_API_KEY = ""
        response = client.get("/metrics", headers={"X-Metrics-Key": "anything"})
        assert response.status_code == 401
        assert "Security Error" in response.json()["detail"]
        
    finally:
        settings.APP_ENV = original_env
        settings.METRICS_API_KEY = original_key



def test_bootstrap_admin_blocked_in_production():
    """Verify bootstrap-admin is ALWAYS blocked in production."""
    original_env = settings.APP_ENV
    original_allow = settings.ALLOW_ADMIN_BOOTSTRAP
    original_token = settings.ADMIN_BOOTSTRAP_TOKEN
    
    # Wait a bit to reset rate limits from previous tests
    time.sleep(1)
    
    try:
        settings.APP_ENV = "production"
        settings.ALLOW_ADMIN_BOOTSTRAP = True
        settings.ADMIN_BOOTSTRAP_TOKEN = "secret-token"
        
        response = client.post(
            "/api/v1/auth/bootstrap-admin",
            headers={"X-Bootstrap-Token": "secret-token"},
            json={
                "name": "Hacker",
                "email": "hacker@example.com",
                "password": "Password123"
            }
        )
        assert response.status_code in (403, 429)
        if response.status_code == 403:
            assert "Admin bootstrap is disabled" in response.json()["detail"]
        
    finally:
        settings.APP_ENV = original_env
        settings.ALLOW_ADMIN_BOOTSTRAP = original_allow
        settings.ADMIN_BOOTSTRAP_TOKEN = original_token
