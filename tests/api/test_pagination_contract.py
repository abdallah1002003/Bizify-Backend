def test_ideas_list_rejects_limit_above_max(client, auth_headers):
    response = client.get("/api/v1/ideas/?limit=101", headers=auth_headers)
    assert response.status_code == 422


def test_ideas_list_rejects_negative_skip(client, auth_headers):
    response = client.get("/api/v1/ideas/?skip=-1", headers=auth_headers)
    assert response.status_code == 422


def test_ideas_list_accepts_valid_pagination(client, auth_headers):
    response = client.get("/api/v1/ideas/?skip=0&limit=5", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

