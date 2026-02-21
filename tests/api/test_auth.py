
def test_create_user_and_login(client):
    # 1. Create a user
    user_payload = {
        "name": "Test User 2",
        "email": "newtest@example.com",
        "password_hash": "securepassword123",
        "role": "entrepreneur",
        "is_active": True,
        "is_verified": False
    }
    
    response = client.post("/api/v1/users/", json=user_payload)
    assert response.status_code in [200, 201]
    
    # 2. Try to login
    login_payload = {
        "username": "newtest@example.com",
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
