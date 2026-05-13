import uuid

from fastapi.testclient import TestClient

from app.models.business import Business, BusinessStage


def _approve_partner_for_user(
    admin_client: TestClient, auth_client: TestClient
) -> str:
    """Submit partner profile for auth_client user and approve via admin; returns profile id."""
    files = {"files": ("test.pdf", b"dummy content", "application/pdf")}
    data = {
        "partner_type": "MENTOR",
        "user_id": str(auth_client.user_id),
        "company_name": "Marketplace Mentor Co",
        "description": "Expert in go-to-market",
    }
    auth_client.post("/api/v1/users/partner-profile", data=data, files=files)

    list_resp = admin_client.get("/api/v1/admin/requests")
    profile_id = next(
        (
            r["id"]
            for r in list_resp.json()
            if r["user_id"] == str(auth_client.user_id)
        ),
        None,
    )
    assert profile_id is not None
    approve_resp = admin_client.patch(f"/api/v1/admin/approve/{profile_id}")
    assert approve_resp.status_code == 200
    return profile_id


def test_marketplace_requires_auth(client: TestClient):
    resp = client.get("/api/v1/marketplace/partners")
    assert resp.status_code == 401


def test_marketplace_list_and_filter_and_detail(
    admin_client: TestClient, auth_client: TestClient, client: TestClient, db_session
):
    """Partner appears after approval; filter and detail work."""
    partner_profile_id = _approve_partner_for_user(admin_client, auth_client)

    # Another pending partner should not appear
    email = f"pending_{uuid.uuid4().hex[:6]}@bizify.com"
    client.post(
        "/api/v1/users/register",
        json={
            "email": email,
            "full_name": "Pending",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    from app.models.user import User

    u = db_session.query(User).filter_by(email=email).first()
    u.is_verified = True
    db_session.commit()
    login = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "Password123!"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    files = {"files": ("x.pdf", b"x", "application/pdf")}
    data = {
        "partner_type": "SUPPLIER",
        "user_id": str(u.id),
        "company_name": "Pending Supplier",
    }
    client.post(
        "/api/v1/users/partner-profile",
        data=data,
        files=files,
        headers=headers,
    )

    # List as entrepreneur (separate user)
    ent = client.post(
        "/api/v1/users/register",
        json={
            "email": f"ent_{uuid.uuid4().hex[:6]}@bizify.com",
            "full_name": "Ent",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    assert ent.status_code == 201
    ent_user = db_session.query(User).filter_by(email=ent.json()["email"]).first()
    ent_user.is_verified = True
    db_session.commit()
    ent_login = client.post(
        "/api/v1/auth/login",
        data={"username": ent.json()["email"], "password": "Password123!"},
    )
    ent_token = ent_login.json()["access_token"]
    ent_headers = {"Authorization": f"Bearer {ent_token}"}

    list_resp = client.get("/api/v1/marketplace/partners", headers=ent_headers)
    assert list_resp.status_code == 200
    ids = {p["id"] for p in list_resp.json()}
    assert partner_profile_id in ids

    filtered = client.get(
        "/api/v1/marketplace/partners?type=MENTOR", headers=ent_headers
    )
    assert filtered.status_code == 200
    assert all(p["partner_type"] == "MENTOR" for p in filtered.json())

    search = client.get(
        "/api/v1/marketplace/partners?q=go-to-market", headers=ent_headers
    )
    assert search.status_code == 200
    assert any(p["id"] == partner_profile_id for p in search.json())

    detail = client.get(
        f"/api/v1/marketplace/partners/{partner_profile_id}",
        headers=ent_headers,
    )
    assert detail.status_code == 200
    assert detail.json()["company_name"] == "Marketplace Mentor Co"
    assert detail.json()["display_name"] is not None


def test_marketplace_create_and_list_requests(
    admin_client: TestClient, auth_client: TestClient, client: TestClient, db_session
):
    """Entrepreneur creates business, requests approved partner, lists requests."""
    partner_profile_id = _approve_partner_for_user(admin_client, auth_client)

    ent_email = f"ent2_{uuid.uuid4().hex[:6]}@bizify.com"
    client.post(
        "/api/v1/users/register",
        json={
            "email": ent_email,
            "full_name": "Biz Owner",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    from app.models.user import User

    ent_user = db_session.query(User).filter_by(email=ent_email).first()
    ent_user.is_verified = True
    db_session.commit()

    ent_login = client.post(
        "/api/v1/auth/login",
        data={"username": ent_email, "password": "Password123!"},
    )
    ent_token = ent_login.json()["access_token"]
    ent_headers = {"Authorization": f"Bearer {ent_token}"}

    biz = Business(owner_id=ent_user.id, stage=BusinessStage.EARLY)
    db_session.add(biz)
    db_session.commit()
    db_session.refresh(biz)

    post = client.post(
        f"/api/v1/marketplace/partners/{partner_profile_id}/requests",
        headers=ent_headers,
        json={"business_id": str(biz.id)},
    )
    assert post.status_code == 201
    body = post.json()
    assert body["partner_id"] == partner_profile_id
    assert body["partner"] is not None
    assert body["partner"]["company_name"] == "Marketplace Mentor Co"

    listed = client.get("/api/v1/marketplace/requests", headers=ent_headers)
    assert listed.status_code == 200
    assert len(listed.json()) >= 1
    assert listed.json()[0]["business_id"] == str(biz.id)


def test_marketplace_cannot_request_self(
    admin_client: TestClient, auth_client: TestClient, db_session
):
    partner_profile_id = _approve_partner_for_user(admin_client, auth_client)

    biz = Business(owner_id=auth_client.user_id, stage=BusinessStage.EARLY)
    db_session.add(biz)
    db_session.commit()
    db_session.refresh(biz)

    resp = auth_client.post(
        f"/api/v1/marketplace/partners/{partner_profile_id}/requests",
        json={"business_id": str(biz.id)},
    )
    assert resp.status_code == 400
    assert "own" in resp.json()["detail"].lower()


def test_marketplace_duplicate_pending_request_fails(
    admin_client: TestClient, auth_client: TestClient, client: TestClient, db_session
):
    partner_profile_id = _approve_partner_for_user(admin_client, auth_client)

    ent_email = f"ent3_{uuid.uuid4().hex[:6]}@bizify.com"
    client.post(
        "/api/v1/users/register",
        json={
            "email": ent_email,
            "full_name": "E",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    from app.models.user import User

    ent_user = db_session.query(User).filter_by(email=ent_email).first()
    ent_user.is_verified = True
    db_session.commit()
    ent_login = client.post(
        "/api/v1/auth/login",
        data={"username": ent_email, "password": "Password123!"},
    )
    ent_headers = {"Authorization": f"Bearer {ent_login.json()['access_token']}"}

    biz = Business(owner_id=ent_user.id, stage=BusinessStage.EARLY)
    db_session.add(biz)
    db_session.commit()
    db_session.refresh(biz)

    url = f"/api/v1/marketplace/partners/{partner_profile_id}/requests"
    assert client.post(
        url, headers=ent_headers, json={"business_id": str(biz.id)}
    ).status_code == 201
    dup = client.post(
        url, headers=ent_headers, json={"business_id": str(biz.id)}
    )
    assert dup.status_code == 400
