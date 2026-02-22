from uuid import uuid4

import app.models as models
import pytest

from config.settings import settings


def _signup(client, email: str, role: str = "entrepreneur"):
    response = client.post(
        "/api/v1/users/",
        json={
            "name": f"user_{uuid4().hex[:6]}",
            "email": email,
            "password": "securepassword123",
            "role": role,
            "is_active": False,
            "is_verified": True,
        },
    )
    assert response.status_code in [200, 201]
    return response.json()


def _login_headers(client, email: str):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "securepassword123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def bootstrap_admin_config():
    old_allow = settings.ALLOW_ADMIN_BOOTSTRAP
    old_token = settings.ADMIN_BOOTSTRAP_TOKEN
    try:
        yield
    finally:
        settings.ALLOW_ADMIN_BOOTSTRAP = old_allow
        settings.ADMIN_BOOTSTRAP_TOKEN = old_token


def test_unauthorized_access_is_blocked(client):
    """Verify that protected API boundaries completely reject unauthorized requests."""
    endpoints = [
        "/api/v1/users/me",
        "/api/v1/businesses/"
    ]
    
    for endpoint in endpoints:
        response = client.get(endpoint)
        # Should return 401 Unauthorized or 422 Unprocessable Entity
        assert response.status_code in [401, 403, 422]


def test_public_signup_cannot_escalate_role(client):
    email = f"escalate_{uuid4().hex[:8]}@example.com"
    user = _signup(client, email=email, role="admin")

    assert user["role"] == "entrepreneur"
    assert user["is_active"] is True
    assert user["is_verified"] is False


def test_user_cannot_delete_another_user(client):
    owner = _signup(client, email=f"owner_{uuid4().hex[:8]}@example.com")
    victim = _signup(client, email=f"victim_{uuid4().hex[:8]}@example.com")

    headers = _login_headers(client, owner["email"])
    response = client.delete(f"/api/v1/users/{victim['id']}", headers=headers)

    assert response.status_code == 403


def test_non_admin_cannot_access_admin_action_logs(client):
    user = _signup(client, email=f"user_{uuid4().hex[:8]}@example.com")
    headers = _login_headers(client, user["email"])

    response = client.get("/api/v1/admin_action_logs/", headers=headers)
    assert response.status_code == 403


def test_non_admin_cannot_list_all_user_profiles(client):
    user = _signup(client, email=f"profile_{uuid4().hex[:8]}@example.com")
    headers = _login_headers(client, user["email"])

    response = client.get("/api/v1/user_profiles/", headers=headers)
    assert response.status_code == 403


def test_user_cannot_access_or_modify_other_user_profile(client, db):
    owner = _signup(client, email=f"owner_profile_{uuid4().hex[:8]}@example.com")
    victim = _signup(client, email=f"victim_profile_{uuid4().hex[:8]}@example.com")
    headers = _login_headers(client, owner["email"])

    victim_profile = (
        db.query(models.UserProfile)
        .filter(models.UserProfile.user_id == victim["id"])
        .first()
    )
    assert victim_profile is not None

    read_response = client.get(f"/api/v1/user_profiles/{victim_profile.id}", headers=headers)
    assert read_response.status_code == 403

    update_response = client.put(
        f"/api/v1/user_profiles/{victim_profile.id}",
        json={"bio": "hacked"},
        headers=headers,
    )
    assert update_response.status_code == 403

    delete_response = client.delete(
        f"/api/v1/user_profiles/{victim_profile.id}",
        headers=headers,
    )
    assert delete_response.status_code == 403


def test_bootstrap_admin_disabled_by_default(client, bootstrap_admin_config):
    settings.ALLOW_ADMIN_BOOTSTRAP = False
    settings.ADMIN_BOOTSTRAP_TOKEN = "bootstrap-secret"

    response = client.post(
        "/api/v1/auth/bootstrap-admin",
        headers={"X-Bootstrap-Token": "bootstrap-secret"},
        json={
            "name": "Bootstrap Admin",
            "email": f"bootstrap_{uuid4().hex[:8]}@example.com",
            "password": "securepassword123",
        },
    )
    assert response.status_code == 403


def test_bootstrap_admin_requires_valid_token(client, bootstrap_admin_config):
    settings.ALLOW_ADMIN_BOOTSTRAP = True
    settings.ADMIN_BOOTSTRAP_TOKEN = "bootstrap-secret"

    response = client.post(
        "/api/v1/auth/bootstrap-admin",
        json={
            "name": "Bootstrap Admin",
            "email": f"bootstrap_{uuid4().hex[:8]}@example.com",
            "password": "securepassword123",
        },
    )
    assert response.status_code == 403

    response = client.post(
        "/api/v1/auth/bootstrap-admin",
        headers={"X-Bootstrap-Token": "wrong-token"},
        json={
            "name": "Bootstrap Admin",
            "email": f"bootstrap_{uuid4().hex[:8]}@example.com",
            "password": "securepassword123",
        },
    )
    assert response.status_code == 403


def test_bootstrap_admin_is_one_time_flow(client, bootstrap_admin_config):
    settings.ALLOW_ADMIN_BOOTSTRAP = True
    settings.ADMIN_BOOTSTRAP_TOKEN = "bootstrap-secret"

    email = f"bootstrap_{uuid4().hex[:8]}@example.com"
    response = client.post(
        "/api/v1/auth/bootstrap-admin",
        headers={"X-Bootstrap-Token": "bootstrap-secret"},
        json={
            "name": "Bootstrap Admin",
            "email": email,
            "password": "securepassword123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "admin"
    assert data["token_type"] == "bearer"
    assert data["access_token"]

    me_response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["role"] == "admin"

    second_response = client.post(
        "/api/v1/auth/bootstrap-admin",
        headers={"X-Bootstrap-Token": "bootstrap-secret"},
        json={
            "name": "Second Admin",
            "email": f"second_{uuid4().hex[:8]}@example.com",
            "password": "securepassword123",
        },
    )
    assert second_response.status_code == 409
