
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
