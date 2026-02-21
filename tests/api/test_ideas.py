from fastapi.testclient import TestClient

def test_create_idea(client: TestClient, auth_headers: dict, test_user: dict):
    # 1. Create an idea (currently unprotected if Idea route doesn't use current_user)
    payload = {
        "owner_id": str(test_user.id),
        "title": "Test Idea",
        "description": "This is a test description",
        "status": "draft",
        "ai_score": 8.5
    }
    response = client.post("/api/v1/ideas/", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Idea"
    assert data["owner_id"] == str(test_user.id)
    assert "id" in data

def test_read_ideas(client: TestClient, auth_headers: dict):
    response = client.get("/api/v1/ideas/", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_read_single_idea(client: TestClient, auth_headers: dict, test_user: dict):
    # 1. Create one
    payload = {
        "owner_id": str(test_user.id),
        "title": "Single Idea",
        "description": "Desc",
        "status": "draft",
        "ai_score": 5.0
    }
    create_res = client.post("/api/v1/ideas/", json=payload, headers=auth_headers)
    idea_id = create_res.json()["id"]
    
    # 2. Get it
    response = client.get(f"/api/v1/ideas/{idea_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == idea_id

def test_update_idea(client: TestClient, auth_headers: dict, test_user: dict):
    # 1. Create one
    payload = {
        "owner_id": str(test_user.id),
        "title": "Update Me",
        "description": "Desc",
        "status": "draft",
        "ai_score": 5.0
    }
    create_res = client.post("/api/v1/ideas/", json=payload, headers=auth_headers)
    idea_id = create_res.json()["id"]
    
    # 2. Update it
    update_payload = {"title": "Updated Title"}
    response = client.put(f"/api/v1/ideas/{idea_id}", json=update_payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"

def test_delete_idea(client: TestClient, auth_headers: dict, test_user: dict):
    # 1. Create one
    payload = {
        "owner_id": str(test_user.id),
        "title": "Delete Me",
        "description": "Desc",
        "status": "draft",
        "ai_score": 5.0
    }
    create_res = client.post("/api/v1/ideas/", json=payload, headers=auth_headers)
    idea_id = create_res.json()["id"]
    
    # 2. Delete it
    response = client.delete(f"/api/v1/ideas/{idea_id}", headers=auth_headers)
    assert response.status_code == 200
    
    # 3. Verify gone
    get_res = client.get(f"/api/v1/ideas/{idea_id}", headers=auth_headers)
    assert get_res.status_code == 404
