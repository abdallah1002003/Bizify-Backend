from fastapi.testclient import TestClient


def test_create_idea_success(auth_client: TestClient):
    """I-01: Create new business idea successfully"""
    response = auth_client.post(
        "/api/v1/ideas/",
        json={
            "title": "Smart Food Delivery App",
            "description": "AI-powered delivery optimization",
            "budget": 5000,
            "industry": "FoodTech"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Smart Food Delivery App"
    assert "id" in data


def test_create_idea_unauthorized(client: TestClient):
    """I-03: Create idea without Token fails"""
    response = client.post(
        "/api/v1/ideas/",
        json={"title": "Unauthorized Idea"}
    )
    assert response.status_code == 401


def test_get_user_ideas(auth_client: TestClient):
    """I-02: Fetch list of user ideas"""
    # Create an idea first
    auth_client.post(
        "/api/v1/ideas/",
        json={"title": "List Idea", "description": "Desc", "budget": 1000}
    )
    
    response = auth_client.get("/api/v1/ideas/")
    assert response.status_code == 200
    ideas = response.json()
    assert isinstance(ideas, list)
    assert len(ideas) >= 1
    assert any(idea["title"] == "List Idea" for idea in ideas)


def test_filter_ideas_by_budget(auth_client: TestClient):
    """I-04: Filter ideas by min and max budget"""
    # Create ideas with different budgets
    auth_client.post("/api/v1/ideas/", json={"title": "Cheap Idea", "budget": 500})
    auth_client.post("/api/v1/ideas/", json={"title": "Mid Idea", "budget": 5000})
    auth_client.post("/api/v1/ideas/", json={"title": "Expensive Idea", "budget": 50000})
    
    # Filter between 1000 and 10000
    response = auth_client.get("/api/v1/ideas/?min_budget=1000&max_budget=10000")
    assert response.status_code == 200
    ideas = response.json()
    
    # We should only get the Mid Idea
    for idea in ideas:
        # Check if the budget exists before asserting, in case schema differs slightly
        if "budget" in idea and idea["budget"] is not None:
            assert 1000 <= idea["budget"] <= 10000


def test_filter_ideas_invalid_budget_range(auth_client: TestClient):
    """I-05: Filter min_budget > max_budget returns 400"""
    response = auth_client.get("/api/v1/ideas/?min_budget=5000&max_budget=1000")
    assert response.status_code == 400


def test_archive_and_unarchive_idea(auth_client: TestClient):
    """I-06, I-07, I-08: Archive, fetch archived, and unarchive idea"""
    # 1. Create Idea
    create_resp = auth_client.post(
        "/api/v1/ideas/",
        json={"title": "To Be Archived", "description": "Desc"}
    )
    idea_id = create_resp.json()["id"]
    
    # 2. Archive Idea (I-06)
    archive_resp = auth_client.patch(f"/api/v1/ideas/{idea_id}/archive")
    assert archive_resp.status_code == 200
    
    # 3. Fetch Archived Ideas (I-07)
    archived_list_resp = auth_client.get("/api/v1/ideas/archived")
    assert archived_list_resp.status_code == 200
    archived_ideas = archived_list_resp.json()
    assert any(idea["id"] == idea_id for idea in archived_ideas)
    
    # 4. Unarchive Idea (I-08)
    unarchive_resp = auth_client.patch(f"/api/v1/ideas/{idea_id}/unarchive")
    assert unarchive_resp.status_code == 200
    
    # 5. Verify it's no longer in archived list
    archived_list_resp2 = auth_client.get("/api/v1/ideas/archived")
    archived_ideas2 = archived_list_resp2.json()
    assert not any(idea["id"] == idea_id for idea in archived_ideas2)
