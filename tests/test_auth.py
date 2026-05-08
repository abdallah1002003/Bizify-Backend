from fastapi.testclient import TestClient


def test_register_user_success(client: TestClient):
    """A-01: Register basic entrepreneur account successfully"""
    response = client.post(
        "/api/v1/users/register",
        json={
            "email": "test1@bizify.com",
            "full_name": "Test User",
            "password": "StrongPassword123!",
            "confirm_password": "StrongPassword123!"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test1@bizify.com"
    assert "id" in data


def test_register_duplicate_email(client: TestClient):
    """A-02: Registering with an already used email returns 400"""
    payload = {
        "email": "test2@bizify.com",
        "full_name": "Test User 2",
        "password": "StrongPassword123!",
        "confirm_password": "StrongPassword123!"
    }
    # First registration
    client.post("/api/v1/users/register", json=payload)
    
    # Second registration with same email
    response = client.post("/api/v1/users/register", json=payload)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_register_password_mismatch(client: TestClient):
    """A-03: Passwords do not match returns 422/400 Validation Error"""
    response = client.post(
        "/api/v1/users/register",
        json={
            "email": "test3@bizify.com",
            "full_name": "Test User",
            "password": "StrongPassword123!",
            "confirm_password": "DifferentPassword123!"
        }
    )
    # FastAPI/Pydantic usually throws 422 for validation, but custom logic might throw 400
    assert response.status_code in [400, 422]


def test_register_invalid_email(client: TestClient):
    """A-04: Invalid email format returns 422"""
    response = client.post(
        "/api/v1/users/register",
        json={
            "email": "not-an-email",
            "full_name": "Test User",
            "password": "StrongPassword123!",
            "confirm_password": "StrongPassword123!"
        }
    )
    assert response.status_code == 422


def test_login_unverified_returns_400(client: TestClient):
    """A-XX: Login with unverified email returns 400"""
    client.post(
        "/api/v1/users/register",
        json={
            "email": "unverified@bizify.com",
            "full_name": "Login User",
            "password": "MySecretPassword1!",
            "confirm_password": "MySecretPassword1!"
        }
    )
    
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "unverified@bizify.com",
            "password": "MySecretPassword1!"
        }
    )
    assert response.status_code == 400
    assert "not verified" in response.json()["detail"].lower()


def test_login_success(client: TestClient, db_session):
    """A-05: Login with valid credentials and verified account returns JWT"""
    from app.models.user import User
    
    client.post(
        "/api/v1/users/register",
        json={
            "email": "login@bizify.com",
            "full_name": "Login User",
            "password": "MySecretPassword1!",
            "confirm_password": "MySecretPassword1!"
        }
    )
    
    # Verify user manually for testing
    user = db_session.query(User).filter_by(email="login@bizify.com").first()
    user.is_verified = True
    db_session.commit()
    
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "login@bizify.com",
            "password": "MySecretPassword1!"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient, db_session):
    """A-06: Login with wrong password returns 401"""
    from app.models.user import User
    
    client.post(
        "/api/v1/users/register",
        json={
            "email": "wrongpass@bizify.com",
            "full_name": "User",
            "password": "CorrectPassword1!",
            "confirm_password": "CorrectPassword1!"
        }
    )
    user = db_session.query(User).filter_by(email="wrongpass@bizify.com").first()
    user.is_verified = True
    db_session.commit()
    
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "wrongpass@bizify.com",
            "password": "WrongPassword1!"
        }
    )
    assert response.status_code == 401


def test_login_nonexistent_email(client: TestClient):
    """A-07: Login with unregistered email returns 401"""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "nobody@bizify.com",
            "password": "Password1!"
        }
    )
    assert response.status_code == 401


def test_session_status_with_token(client: TestClient, db_session):
    """A-10: Get session status with valid token"""
    from app.models.user import User
    
    client.post(
        "/api/v1/users/register",
        json={
            "email": "session@bizify.com",
            "full_name": "User",
            "password": "Password1!",
            "confirm_password": "Password1!"
        }
    )
    user = db_session.query(User).filter_by(email="session@bizify.com").first()
    user.is_verified = True
    db_session.commit()
    
    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "session@bizify.com", "password": "Password1!"}
    )
    token = login_resp.json()["access_token"]
    
    response = client.get(
        "/api/v1/auth/session-status",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "is_active" in data
    assert data["is_active"] is True


def test_session_status_without_token(client: TestClient):
    """A-09: Session status without token fails"""
    response = client.get("/api/v1/auth/session-status")
    assert response.status_code == 401


def test_logout_invalidates_token(client: TestClient, db_session):
    """A-11: Logout invalidates the current session token"""
    from app.models.user import User
    
    client.post(
        "/api/v1/users/register",
        json={
            "email": "logout@bizify.com",
            "full_name": "User",
            "password": "Password1!",
            "confirm_password": "Password1!"
        }
    )
    user = db_session.query(User).filter_by(email="logout@bizify.com").first()
    user.is_verified = True
    db_session.commit()
    
    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "logout@bizify.com", "password": "Password1!"}
    )
    token = login_resp.json()["access_token"]
    
    # 1. Logout
    logout_resp = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert logout_resp.status_code == 200
    
    # 2. Try to use token after logout
    status_resp = client.get(
        "/api/v1/auth/session-status",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert status_resp.status_code == 401


