from uuid import uuid4


def _create_and_login_user(client, email: str, password: str) -> dict:
    user_payload = {
        "name": f"User {email}",
        "email": email,
        "password": password,
        "is_active": True,
        "is_verified": True,
    }
    create_res = client.post("/api/v1/users/", json=user_payload)
    assert create_res.status_code in [200, 201]

    login_res = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_full_business_creation_workflow(client, auth_headers):
    me_res = client.get("/api/v1/users/me", headers=auth_headers)
    assert me_res.status_code == 200
    current_user_id = me_res.json()["id"]

    idea_payload = {
        "owner_id": str(uuid4()),  # route should enforce current user as owner
        "title": "Workflow Idea",
        "description": "End-to-end test idea",
        "status": "draft",
        "ai_score": 0.25,
    }
    idea_res = client.post("/api/v1/ideas/", json=idea_payload, headers=auth_headers)
    assert idea_res.status_code == 200
    idea_data = idea_res.json()
    assert idea_data["owner_id"] == current_user_id

    biz_payload = {
        "owner_id": str(uuid4()),  # route should enforce current user as owner
        "idea_id": idea_data["id"],
        "stage": "early",
    }
    biz_res = client.post("/api/v1/businesses/", json=biz_payload, headers=auth_headers)
    assert biz_res.status_code == 200
    biz_data = biz_res.json()
    assert biz_data["owner_id"] == current_user_id
    assert biz_data["stage"] == "early"

    roadmap_list_res = client.get("/api/v1/business_roadmaps/", headers=auth_headers)
    assert roadmap_list_res.status_code == 200
    roadmaps = roadmap_list_res.json()
    roadmap = next((r for r in roadmaps if r["business_id"] == biz_data["id"]), None)
    assert roadmap is not None

    stage_payload = {
        "roadmap_id": roadmap["id"],
        "order_index": 1,
        "stage_type": "market",
        "status": "planned",
        "output_json": {"source": "integration"},
    }
    stage_res = client.post("/api/v1/roadmap_stages/", json=stage_payload, headers=auth_headers)
    assert stage_res.status_code == 200
    stage_data = stage_res.json()
    assert stage_data["status"] == "planned"

    stage_update_res = client.put(
        f"/api/v1/roadmap_stages/{stage_data['id']}",
        json={"status": "completed"},
        headers=auth_headers,
    )
    assert stage_update_res.status_code == 200
    assert stage_update_res.json()["status"] == "completed"

    refreshed_roadmap_res = client.get(f"/api/v1/business_roadmaps/{roadmap['id']}", headers=auth_headers)
    assert refreshed_roadmap_res.status_code == 200
    assert refreshed_roadmap_res.json()["completion_percentage"] > 0


def test_cross_user_resource_isolation_for_secured_modules(client, auth_headers):
    owner_res = client.get("/api/v1/users/me", headers=auth_headers)
    assert owner_res.status_code == 200
    owner_id = owner_res.json()["id"]

    other_email = f"user_{uuid4().hex[:8]}@example.com"
    other_headers = _create_and_login_user(client, other_email, "strongpass123")
    other_me_res = client.get("/api/v1/users/me", headers=other_headers)
    assert other_me_res.status_code == 200
    other_id = other_me_res.json()["id"]

    notification_res = client.post(
        "/api/v1/notifications/",
        json={"user_id": other_id, "title": "hello", "message": "owner-only"},
        headers=auth_headers,
    )
    assert notification_res.status_code == 200
    notification_data = notification_res.json()
    assert notification_data["user_id"] == owner_id

    owner_read = client.get(f"/api/v1/notifications/{notification_data['id']}", headers=auth_headers)
    other_read = client.get(f"/api/v1/notifications/{notification_data['id']}", headers=other_headers)
    assert owner_read.status_code == 200
    assert other_read.status_code == 403

    session_res = client.post(
        "/api/v1/chat_sessions/",
        json={"user_id": other_id, "session_type": "idea_chat"},
        headers=auth_headers,
    )
    assert session_res.status_code == 200
    session_data = session_res.json()
    assert session_data["user_id"] == owner_id

    owner_session = client.get(f"/api/v1/chat_sessions/{session_data['id']}", headers=auth_headers)
    other_session = client.get(f"/api/v1/chat_sessions/{session_data['id']}", headers=other_headers)
    assert owner_session.status_code == 200
    assert other_session.status_code == 403

    payment_method_res = client.post(
        "/api/v1/payment_methods/",
        json={
            "user_id": other_id,
            "provider": "stripe",
            "token_ref": "tok_123",
            "last4": "4242",
            "is_default": True,
        },
        headers=auth_headers,
    )
    assert payment_method_res.status_code == 200
    payment_method_data = payment_method_res.json()
    assert payment_method_data["user_id"] == owner_id

    owner_payment_method = client.get(f"/api/v1/payment_methods/{payment_method_data['id']}", headers=auth_headers)
    other_payment_method = client.get(f"/api/v1/payment_methods/{payment_method_data['id']}", headers=other_headers)
    assert owner_payment_method.status_code == 200
    assert other_payment_method.status_code == 403
