from fastapi.testclient import TestClient

def test_create_business(client: TestClient, auth_headers: dict, test_user: dict):
    # 1. Create a business
    payload = {
        "owner_id": str(test_user.id),
        "stage": "early"
    }
    response = client.post("/api/v1/businesses/", json=payload, headers=auth_headers)
    if response.status_code != 200:
        print("ERROR RESPONSE:", response.json())
    assert response.status_code == 200
    data = response.json()
    assert data["owner_id"] == str(test_user.id)
    assert data["stage"] == "early"
    assert "id" in data

def test_read_businesses(client: TestClient, auth_headers: dict):
    response = client.get("/api/v1/businesses/", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_read_single_business(client: TestClient, auth_headers: dict, test_user: dict):
    # 1. Create one
    payload = {
        "owner_id": str(test_user.id),
        "stage": "building"
    }
    create_res = client.post("/api/v1/businesses/", json=payload, headers=auth_headers)
    biz_id = create_res.json()["id"]
    
    # 2. Get it
    response = client.get(f"/api/v1/businesses/{biz_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == biz_id

def test_update_business(client: TestClient, auth_headers: dict, test_user: dict):
    # 1. Create one
    payload = {
        "owner_id": str(test_user.id),
        "stage": "early"
    }
    create_res = client.post("/api/v1/businesses/", json=payload, headers=auth_headers)
    biz_id = create_res.json()["id"]
    
    # 2. Update it
    update_payload = {"stage": "scaling"}
    response = client.put(f"/api/v1/businesses/{biz_id}", json=update_payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["stage"] == "scaling"

def test_delete_business(client: TestClient, auth_headers: dict, test_user: dict):
    # 1. Create one
    payload = {
        "owner_id": str(test_user.id),
        "stage": "early"
    }
    create_res = client.post("/api/v1/businesses/", json=payload, headers=auth_headers)
    biz_id = create_res.json()["id"]
    
    # 2. Delete it
    response = client.delete(f"/api/v1/businesses/{biz_id}", headers=auth_headers)
    assert response.status_code == 200
    
    # 3. Verify gone
    get_res = client.get(f"/api/v1/businesses/{biz_id}", headers=auth_headers)
    assert get_res.status_code == 404
