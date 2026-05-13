import json
import uuid

from fastapi.testclient import TestClient


def test_update_user_profile_success(auth_client: TestClient):
    """U-03: Update base user profile successfully"""
    response = auth_client.post(
        "/api/v1/users/profile",
        json={
            "bio": "This is a test bio",
            "skills_json": [{"name": "Python", "rating": 5}]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["bio"] == "This is a test bio"


def test_update_user_profile_unauthorized(client: TestClient):
    """U-0X: Update profile without token is rejected"""
    response = client.post(
        "/api/v1/users/profile",
        json={"bio": "Hacked bio"}
    )
    assert response.status_code == 401


def test_get_partner_profile_not_found(auth_client: TestClient):
    """U-06 (Not Found): Fetching a partner profile when none exists returns 404"""
    response = auth_client.get("/api/v1/users/partner-profile")
    assert response.status_code == 404


def test_create_partner_profile_success(auth_client: TestClient):
    """U-04: Create a secondary partner profile using multipart/form-data"""
    # Create a dummy file for the upload
    files = {
        "files": ("test_doc.pdf", b"dummy pdf content", "application/pdf")
    }
    
    # Form data for multipart/form-data request
    data = {
        "partner_type": "MENTOR",
        "user_id": str(auth_client.user_id),
        "company_name": "Tech Mentors Inc.",
        "description": "Helping startups grow",
        "services_json": json.dumps(["Consulting", "Code Review"])
    }
    
    response = auth_client.post(
        "/api/v1/users/partner-profile",
        data=data,
        files=files
    )
    
    assert response.status_code == 200
    resp_data = response.json()
    assert resp_data["partner_type"] == "MENTOR"
    assert resp_data["company_name"] == "Tech Mentors Inc."
    assert "approval_status" in resp_data


def test_create_partner_profile_idor_protection(auth_client: TestClient):
    """U-05 IDOR: Attempting to create a profile for another user returns 403"""
    files = {
        "files": ("test_doc.pdf", b"dummy pdf content", "application/pdf")
    }
    
    # Using a fake UUID that is not auth_client.user_id
    fake_user_id = str(uuid.uuid4())
    
    data = {
        "partner_type": "MENTOR",
        "user_id": fake_user_id,
    }
    
    response = auth_client.post(
        "/api/v1/users/partner-profile",
        data=data,
        files=files
    )
    
    assert response.status_code == 403
    assert "must match the authenticated user" in response.json()["detail"].lower()


def test_get_partner_profile_success(auth_client: TestClient):
    """U-06: Fetch partner profile successfully"""
    # 1. Create it first
    files = {"files": ("test_doc.pdf", b"dummy content", "application/pdf")}
    data = {
        "partner_type": "SUPPLIER",
        "user_id": str(auth_client.user_id),
        "company_name": "Supply Co"
    }
    auth_client.post("/api/v1/users/partner-profile", data=data, files=files)
    
    # 2. Get it
    response = auth_client.get("/api/v1/users/partner-profile")
    assert response.status_code == 200
    assert response.json()["company_name"] == "Supply Co"


def test_update_partner_profile(auth_client: TestClient):
    """U-05: Update existing partner profile"""
    # 1. Create it first
    files = {"files": ("test_doc.pdf", b"dummy content", "application/pdf")}
    data = {
        "partner_type": "MANUFACTURER",
        "user_id": str(auth_client.user_id),
        "company_name": "Old Name"
    }
    auth_client.post("/api/v1/users/partner-profile", data=data, files=files)
    
    # 2. Update it
    response = auth_client.patch(
        "/api/v1/users/partner-profile",
        json={"company_name": "New Name Updated"}
    )
    
    assert response.status_code == 200
    assert response.json()["company_name"] == "New Name Updated"

