from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient


# Mock response that the AI pipeline service would return
MOCK_AI_RESULT = {
    "business_ideas": [
        {"title": "AI Coffee Shop", "score": 92, "summary": "Premium AI-assisted coffee experience"}
    ],
    "skill_gaps": ["Marketing", "Finance"],
    "recommended_mentors": []
}

MOCK_STATUS = {"status": "completed", "progress": 100}


def test_run_ai_pipeline(auth_client: TestClient):
    """AI-01: Trigger AI analysis pipeline (mocked external call)"""
    with patch(
        "app.services.ai_pipeline_service.AIPipelineService.run",
        new_callable=AsyncMock,
        return_value=MOCK_AI_RESULT
    ):
        resp = auth_client.post("/api/v1/ai/analyze")

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "result" in data


def test_ai_pipeline_no_profile(auth_client: TestClient):
    """AI-02: Pipeline handles missing profile gracefully"""
    # Without mocking, the service will fail to reach the external AI server
    # We expect 502 (Bad Gateway) or 503 (Service Unavailable) — not a 500 crash
    resp = auth_client.post("/api/v1/ai/analyze")
    assert resp.status_code in [200, 502, 503]


def test_get_ai_pipeline_status(auth_client: TestClient):
    """AI-03: Check AI pipeline progress status (mocked)"""
    with patch(
        "app.services.ai_pipeline_service.AIPipelineService.get_status",
        new_callable=AsyncMock,
        return_value=MOCK_STATUS
    ):
        resp = auth_client.get("/api/v1/ai/analyze/status")

    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data


def test_get_ai_pipeline_results(auth_client: TestClient):
    """AI-04: Fetch completed AI results and save to DB (mocked)"""
    with patch(
        "app.services.ai_pipeline_service.AIPipelineService.get_results",
        new_callable=AsyncMock,
        return_value=MOCK_AI_RESULT
    ):
        resp = auth_client.get("/api/v1/ai/analyze/results")

    assert resp.status_code == 200
    data = resp.json()
    assert "business_ideas" in data or "skill_gaps" in data


def test_ai_pipeline_unauthorized(client: TestClient):
    """AI-05: AI pipeline without token is rejected"""
    resp = client.post("/api/v1/ai/analyze")
    assert resp.status_code == 401


def test_ai_status_unauthorized(client: TestClient):
    """AI-06: AI status without token is rejected"""
    resp = client.get("/api/v1/ai/analyze/status")
    assert resp.status_code == 401


def test_ai_results_unauthorized(client: TestClient):
    """AI-07: AI results without token is rejected"""
    resp = client.get("/api/v1/ai/analyze/results")
    assert resp.status_code == 401
