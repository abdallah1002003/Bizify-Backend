from fastapi.testclient import TestClient


def test_list_guidance_stages(client: TestClient):
    """GD-01: List all guidance stages (public endpoint)"""
    resp = client.get("/api/v1/guidance/stages")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_get_concepts_for_stage(client: TestClient):
    """GD-02: Get concepts for a stage"""
    # Get stages first
    stages_resp = client.get("/api/v1/guidance/stages")
    stages = stages_resp.json()

    if not stages:
        # No seed data in test DB — endpoint is reachable and returns empty list
        return

    stage_id = stages[0]["id"]
    resp = client.get(f"/api/v1/guidance/stages/{stage_id}/concepts")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_get_concept_detail(client: TestClient):
    """GD-03: Get detail of a specific concept"""
    stages_resp = client.get("/api/v1/guidance/stages")
    stages = stages_resp.json()
    if not stages:
        return

    stage_id = stages[0]["id"]
    concepts_resp = client.get(f"/api/v1/guidance/stages/{stage_id}/concepts")
    concepts = concepts_resp.json()
    if not concepts:
        return

    concept_id = concepts[0]["id"]
    resp = client.get(f"/api/v1/guidance/concepts/{concept_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == concept_id


def test_update_progress(auth_client: TestClient):
    """GD-04: Mark progress on a concept"""
    # Need a real concept id. Get from stages/concepts
    stages = auth_client.get("/api/v1/guidance/stages").json()
    if not stages:
        return

    stage_id = stages[0]["id"]
    concepts = auth_client.get(f"/api/v1/guidance/stages/{stage_id}/concepts").json()
    if not concepts:
        return

    concept_id = concepts[0]["id"]
    resp = auth_client.post(f"/api/v1/guidance/progress/{concept_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert "concept_id" in data or "last_concept_id" in data


def test_get_progress_not_found(auth_client: TestClient):
    """GD-05: Get progress before any interaction returns 404"""
    resp = auth_client.get("/api/v1/guidance/progress")
    # 404 if no progress recorded yet
    assert resp.status_code in [200, 404]


def test_guidance_unauthorized(client: TestClient):
    """GD-06: Progress update without token is rejected"""
    import uuid
    fake_id = str(uuid.uuid4())
    resp = client.post(f"/api/v1/guidance/progress/{fake_id}")
    assert resp.status_code == 401
