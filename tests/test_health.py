from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """
    Test H-01: Root endpoint returns a simple welcome message.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World!"}


def test_health_check(client: TestClient):
    """
    Test H-02: Health check endpoint returns healthy status and project name.
    """
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "project_name" in data
    assert data["project_name"] == "Bizify"
