import uuid

from fastapi.testclient import TestClient


def test_request_export_success(auth_client: TestClient):
    """EX-01: Request a data export job"""
    resp = auth_client.post(
        "/api/v1/export/",
        json={"scope": ["ideas"], "format": "json"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
    assert data["status"] in ["PENDING", "pending", "PROCESSING", "processing"]


def test_get_export_status(auth_client: TestClient):
    """EX-02: Get status of an existing export job"""
    create_resp = auth_client.post(
        "/api/v1/export/",
        json={"scope": ["ideas"], "format": "json"}
    )
    job_id = create_resp.json()["id"]

    resp = auth_client.get(f"/api/v1/export/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == job_id


def test_get_export_status_not_found(auth_client: TestClient):
    """EX-03: Get status of non-existent export job returns 404"""
    fake_id = str(uuid.uuid4())
    resp = auth_client.get(f"/api/v1/export/{fake_id}")
    assert resp.status_code == 404


def test_cancel_export_job(auth_client: TestClient):
    """EX-04: Cancel an export job"""
    create_resp = auth_client.post(
        "/api/v1/export/",
        json={"scope": ["ideas"], "format": "json"}
    )
    job_id = create_resp.json()["id"]

    resp = auth_client.post(f"/api/v1/export/{job_id}/cancel")
    assert resp.status_code in [200, 400]


def test_download_export_not_ready(auth_client: TestClient):
    """EX-05: Download an export that is not yet completed returns 400"""
    create_resp = auth_client.post(
        "/api/v1/export/",
        json={"scope": ["ideas"], "format": "json"}
    )
    job_id = create_resp.json()["id"]

    resp = auth_client.get(f"/api/v1/export/{job_id}/download")
    assert resp.status_code in [400, 410]


def test_export_unauthorized(client: TestClient):
    """EX-06: Export without token is rejected"""
    resp = client.post("/api/v1/export/", json={"scope": ["ideas"], "format": "json"})
    assert resp.status_code == 401
