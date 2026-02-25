import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid

from main import app
from app.models.users.user import User

def test_full_user_journey(client: TestClient, db: Session):
    # 1. Sign Up
    email = f"e2e_{uuid.uuid4().hex[:6]}@example.com"
    password = "e2estronGPassword!23"
    
    signup_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "name": "E2E User"
        }
    )
    assert signup_resp.status_code == 201, f"Signup failed: {signup_resp.text}"
    user_data = signup_resp.json()
    assert "id" in user_data
    
    # 2. Email Verification via Database
    user = db.query(User).filter(User.email == email).first()
    assert user is not None
    assert user.is_verified is False
    
    # Simulate DB-level email confirmation since we don't have access to the actual email inbox in tests
    user.is_verified = True
    db.commit()
    
    # 3. Login
    login_resp = client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": password
        }
    )
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token_data = login_resp.json()
    assert "access_token" in token_data
    access_token = token_data["access_token"]
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Verify identity (First API Call acting identically to normal usage)
    me_resp = client.get(
        "/api/v1/users/me",
        headers=headers
    )
    assert me_resp.status_code == 200, f"Get /me failed: {me_resp.text}"
    assert me_resp.json()["email"] == email
    
    # 4. Work: Create Business 
    bus_resp = client.post(
        "/api/v1/businesses/",
        headers=headers,
        json={
            "owner_id": user_data["id"],
            "stage": "early",
            "context_json": {"name": "E2E Dream Company", "description": "Building stuff dynamically"}
        }
    )
    assert bus_resp.status_code in [200, 201], f"Business creation failed: {bus_resp.text}"
    business_id = bus_resp.json()["id"]
    
    # Get Businesses to verify List response length
    bus_list_resp = client.get(
        "/api/v1/businesses/",
        headers=headers
    )
    assert bus_list_resp.status_code == 200
    assert len(bus_list_resp.json()) >= 1
    
    # 5. Logout
    logout_resp = client.post(
        "/api/v1/auth/logout",
        headers=headers,
        json={"refresh_token": token_data["refresh_token"]}
    )
    assert logout_resp.status_code == 200
    
    # Verify Logout Effect (Blacklisting JTI works)
    bus_list_resp_after = client.get(
        "/api/v1/businesses/",
        headers=headers
    )
    # The JTI blacklisting means this token is rejected explicitly
    assert bus_list_resp_after.status_code == 401
