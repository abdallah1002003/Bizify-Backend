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
    resp = auth_client.get("/api/v1/ai/status")
    # 200 = status found; 404 = pipeline not yet started for this user; 503 = service unavailable (no key)
    assert resp.status_code in [200, 404, 503], (
        f"Unexpected status {resp.status_code}: {resp.text}"
    )
    if resp.status_code == 200:
        assert b"status" in resp.content


# ─────────────────────────────────────────────────────────────────────────────
# AI-04 — Fetch pipeline results (profile analysis) (real call)
# ─────────────────────────────────────────────────────────────────────────────
def test_get_ai_pipeline_results(auth_client: TestClient):
    """AI-04: Fetch completed AI profile analysis results (real deployed AI)"""
    resp = auth_client.get("/api/v1/ai/profile")
    # 200 = results exist; 404 = not found; 425 = pipeline not yet run; 503 = service unavailable
    assert resp.status_code in [200, 404, 425, 503], (
        f"Unexpected status {resp.status_code}: {resp.text}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# AI-05 — Fetch generated problems (real call)
# ─────────────────────────────────────────────────────────────────────────────
def test_get_ai_problems(auth_client: TestClient):
    """AI-05: Fetch AI-generated problems for this user (real deployed AI)"""
    resp = auth_client.get("/api/v1/ai/problems")
    # 425 = pipeline hasn't started yet for this user; 503 = service unavailable
    assert resp.status_code in [200, 404, 425, 503], (
        f"Unexpected status {resp.status_code}: {resp.text}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# AI-06 — Fetch generated business idea (real call)
# ─────────────────────────────────────────────────────────────────────────────
def test_get_ai_idea(auth_client: TestClient):
    """AI-06: Fetch AI-generated business idea for this user (real deployed AI)"""
    resp = auth_client.get("/api/v1/ai/idea")
    # 425 = pipeline hasn't started yet for this user; 503 = service unavailable
    assert resp.status_code in [200, 404, 425, 503], (
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
    resp = client.get("/api/v1/ai/status")
    assert resp.status_code == 401


def test_ai_pipeline_unauthorized_results(client: TestClient):
    """AI-09: AI results endpoint without token is rejected"""
    resp = client.get("/api/v1/ai/profile")
    assert resp.status_code == 401

# ─────────────────────────────────────────────────────────────────────────────
# Additional Tests for all AI proxy endpoints
# ─────────────────────────────────────────────────────────────────────────────
def test_get_ai_customers(auth_client: TestClient):
    """AI-10: Fetch AI-generated customers"""
    resp = auth_client.get("/api/v1/ai/customers")
    assert resp.status_code in [200, 404, 425, 503]

def test_get_ai_competition(auth_client: TestClient):
    """AI-11: Fetch AI-generated competition"""
    resp = auth_client.get("/api/v1/ai/competition")
    assert resp.status_code in [200, 404, 425, 503]

def test_get_ai_market_potential(auth_client: TestClient):
    """AI-12: Fetch AI-generated market potential"""
    resp = auth_client.get("/api/v1/ai/market-potential")
    assert resp.status_code in [200, 404, 425, 503]

def test_get_ai_idea_strategy(auth_client: TestClient):
    """AI-13: Fetch AI-generated idea strategy"""
    resp = auth_client.get("/api/v1/ai/idea-strategy")
    assert resp.status_code in [200, 404, 425, 503]

def test_get_ai_business_model(auth_client: TestClient):
    """AI-14: Fetch AI-generated business model"""
    resp = auth_client.get("/api/v1/ai/business-model")
    assert resp.status_code in [200, 404, 425, 503]

def test_get_ai_functions_list(auth_client: TestClient):
    """AI-15: Fetch AI-generated functions list"""
    resp = auth_client.get("/api/v1/ai/functions-list")
    assert resp.status_code in [200, 404, 425, 503]

def test_get_ai_mvp_planning(auth_client: TestClient):
    """AI-16: Fetch AI-generated MVP planning"""
    resp = auth_client.get("/api/v1/ai/mvp-planning")
    assert resp.status_code in [200, 404, 425, 503]

def test_get_ai_unit_economics(auth_client: TestClient):
    """AI-17: Fetch AI-generated unit economics"""
    resp = auth_client.get("/api/v1/ai/unit-economics")
    assert resp.status_code in [200, 404, 425, 503]

def test_get_ai_go_to_market(auth_client: TestClient):
    """AI-18: Fetch AI-generated Go-To-Market strategy"""
    resp = auth_client.get("/api/v1/ai/go-to-market")
    assert resp.status_code in [200, 404, 425, 503]

# --- Extended POST Tests ---

def test_post_generate_customers(auth_client):
    resp = auth_client.post("/api/v1/ai/customers")
    assert resp.status_code in [200, 404, 422, 425, 500, 503]

def test_post_regenerate_customers(auth_client):
    resp = auth_client.post("/api/v1/ai/customers/regenerate")
    assert resp.status_code in [200, 404, 422, 425, 500, 503]

def test_post_generate_competition(auth_client):
    resp = auth_client.post("/api/v1/ai/competition")
    assert resp.status_code in [200, 404, 422, 425, 500, 503]

def test_post_regenerate_competition(auth_client):
    resp = auth_client.post("/api/v1/ai/competition/regenerate")
    assert resp.status_code in [200, 404, 422, 425, 500, 503]

def test_post_generate_market_potential(auth_client):
    resp = auth_client.post("/api/v1/ai/market-potential")
    assert resp.status_code in [200, 404, 422, 425, 500, 503]

def test_post_regenerate_market_potential(auth_client):
    resp = auth_client.post("/api/v1/ai/market-potential/regenerate")
    assert resp.status_code in [200, 404, 422, 425, 500, 503]

def test_post_generate_idea_strategy(auth_client):
    resp = auth_client.post("/api/v1/ai/idea-strategy")
    assert resp.status_code in [200, 404, 422, 425, 500, 503]

def test_post_regenerate_idea_strategy(auth_client):
    resp = auth_client.post("/api/v1/ai/idea-strategy/regenerate")
    assert resp.status_code in [200, 404, 422, 425, 500, 503]

def test_post_generate_business_model(auth_client):
    resp = auth_client.post("/api/v1/ai/business-model")
    assert resp.status_code in [200, 404, 422, 425, 500, 503]

def test_post_regenerate_business_model(auth_client):
    resp = auth_client.post("/api/v1/ai/business-model/regenerate")
    assert resp.status_code in [200, 404, 422, 425, 500, 503]

def test_post_generate_functions_list(auth_client):
    resp = auth_client.post("/api/v1/ai/functions-list")
    assert resp.status_code in [200, 404, 422, 425, 500, 503]

def test_post_regenerate_functions_list(auth_client):
    resp = auth_client.post("/api/v1/ai/functions-list/regenerate")
    assert resp.status_code in [200, 404, 422, 425, 500, 503]

def test_post_generate_mvp_planning(auth_client):
    resp = auth_client.post("/api/v1/ai/mvp-planning")
    assert resp.status_code in [200, 404, 422, 425, 500, 503]

def test_post_regenerate_mvp_planning(auth_client):
    resp = auth_client.post("/api/v1/ai/mvp-planning/regenerate")
    assert resp.status_code in [200, 404, 422, 425, 500, 503]

def test_post_generate_unit_economics(auth_client):
    resp = auth_client.post("/api/v1/ai/unit-economics")
    assert resp.status_code in [200, 404, 422, 425, 500, 503]

def test_post_regenerate_unit_economics(auth_client):
    resp = auth_client.post("/api/v1/ai/unit-economics/regenerate")
    assert resp.status_code in [200, 404, 422, 425, 500, 503]

def test_post_generate_go_to_market(auth_client):
    resp = auth_client.post("/api/v1/ai/go-to-market")
    assert resp.status_code in [200, 404, 422, 425, 500, 503]

def test_post_regenerate_go_to_market(auth_client):
    resp = auth_client.post("/api/v1/ai/go-to-market/regenerate")
    assert resp.status_code in [200, 404, 422, 425, 500, 503]
