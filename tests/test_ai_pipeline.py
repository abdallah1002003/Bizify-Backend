"""
AI Pipeline Integration Tests
==============================
These tests call the REAL deployed AI pipeline at:
  https://bizifyai-production.up.railway.app

All requests go through the secure Bizify proxy at /api/v1/ai/...
which validates the JWT, injects the x-api-key, and overrides user_id.

Real endpoint mappings (proxy → external AI):
  POST /api/v1/ai/run                 → POST /pipeline/run
  GET  /api/v1/ai/status/{user_id}    → GET  /pipeline/status/{user_id}
  GET  /api/v1/ai/profile/{user_id}   → GET  /pipeline/profile/{user_id}
  GET  /api/v1/ai/problems/{user_id}  → GET  /pipeline/problems/{user_id}
  GET  /api/v1/ai/idea/{user_id}      → GET  /pipeline/idea/{user_id}
"""
from fastapi.testclient import TestClient


# ─────────────────────────────────────────────────────────────────────────────
# AI-01 — Trigger the full AI pipeline (real call)
# ─────────────────────────────────────────────────────────────────────────────
def test_run_ai_pipeline(auth_client: TestClient):
    """AI-01: Trigger AI analysis pipeline (real call to deployed AI service)"""
    resp = auth_client.post("/api/v1/ai/run")
    # 200 = pipeline started; 422 = missing required profile data
    assert resp.status_code in [200, 422, 503], (
        f"Unexpected status {resp.status_code}: {resp.text}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# AI-02 — Trigger pipeline with no profile (should handle gracefully)
# ─────────────────────────────────────────────────────────────────────────────
def test_ai_pipeline_no_profile(auth_client: TestClient):
    """AI-02: Pipeline handles new user with no profile gracefully"""
    resp = auth_client.post("/api/v1/ai/run")
    # Should never be a 500 — a graceful 422/503/200 is all acceptable
    assert resp.status_code != 500, (
        f"Pipeline crashed with 500: {resp.text}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# AI-03 — Check pipeline status for the authenticated user (real call)
# ─────────────────────────────────────────────────────────────────────────────
def test_get_ai_pipeline_status(auth_client: TestClient):
    """AI-03: Check AI pipeline progress status (real deployed AI)"""
    user_id = str(auth_client.user_id)
    resp = auth_client.get(f"/api/v1/ai/status/{user_id}")
    # 200 = status found; 404 = pipeline not yet started for this user
    assert resp.status_code in [200, 404], (
        f"Unexpected status {resp.status_code}: {resp.text}"
    )
    if resp.status_code == 200:
        assert b"status" in resp.content


# ─────────────────────────────────────────────────────────────────────────────
# AI-04 — Fetch pipeline results (profile analysis) (real call)
# ─────────────────────────────────────────────────────────────────────────────
def test_get_ai_pipeline_results(auth_client: TestClient):
    """AI-04: Fetch completed AI profile analysis results (real deployed AI)"""
    user_id = str(auth_client.user_id)
    resp = auth_client.get(f"/api/v1/ai/profile/{user_id}")
    # 200 = results exist; 404 = not found; 425 = pipeline not yet run for this user
    assert resp.status_code in [200, 404, 425], (
        f"Unexpected status {resp.status_code}: {resp.text}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# AI-05 — Fetch generated problems (real call)
# ─────────────────────────────────────────────────────────────────────────────
def test_get_ai_problems(auth_client: TestClient):
    """AI-05: Fetch AI-generated problems for this user (real deployed AI)"""
    user_id = str(auth_client.user_id)
    resp = auth_client.get(f"/api/v1/ai/problems/{user_id}")
    # 425 = pipeline hasn't started yet for this user
    assert resp.status_code in [200, 404, 425], (
        f"Unexpected status {resp.status_code}: {resp.text}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# AI-06 — Fetch generated business idea (real call)
# ─────────────────────────────────────────────────────────────────────────────
def test_get_ai_idea(auth_client: TestClient):
    """AI-06: Fetch AI-generated business idea for this user (real deployed AI)"""
    user_id = str(auth_client.user_id)
    resp = auth_client.get(f"/api/v1/ai/idea/{user_id}")
    # 425 = pipeline hasn't started yet for this user
    assert resp.status_code in [200, 404, 425], (
        f"Unexpected status {resp.status_code}: {resp.text}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Security tests — should never reach the AI server at all
# ─────────────────────────────────────────────────────────────────────────────
def test_ai_pipeline_unauthorized(client: TestClient):
    """AI-07: AI pipeline without token is rejected before reaching AI server"""
    resp = client.post("/api/v1/ai/run")
    assert resp.status_code == 401


def test_ai_pipeline_unauthorized_status(client: TestClient):
    """AI-08: AI status endpoint without token is rejected"""
    resp = client.get("/api/v1/ai/status/some-user-id")
    assert resp.status_code == 401


def test_ai_pipeline_unauthorized_results(client: TestClient):
    """AI-09: AI results endpoint without token is rejected"""
    resp = client.get("/api/v1/ai/profile/some-user-id")
    assert resp.status_code == 401
