import uuid

def test_create_user_and_login(client):
    # 1. Create a user via /auth/register
    email = f"auth_{uuid.uuid4().hex[:8]}@example.com"
    user_payload = {
        "name": "Test User 2",
        "email": email,
        "password": "securepassword123",
        "role": "entrepreneur"
    }
    
    response = client.post("/api/v1/auth/register", json=user_payload)
    assert response.status_code == 201
    
    # 2. Try to login
    login_payload = {
        "username": email,
        "password": "securepassword123"
    }
    
    response = client.post("/api/v1/auth/login", data=login_payload)
    assert response.status_code == 200
    token = response.json().get("access_token")
    assert token is not None

def test_protected_route_without_token(client):
    # Attempt to browse businesses without Auth Header
    response = client.get("/api/v1/businesses/")
    assert response.status_code == 401
