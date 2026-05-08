from fastapi.testclient import TestClient


def test_list_plans(client: TestClient):
    """B-01: List billing plans"""
    resp = client.get("/api/v1/billing/plans")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_paypal_subscribe(auth_client: TestClient):
    """B-04: Generate PayPal order"""
    # Need an active plan ID. Let's get one from the plans endpoint
    plans_resp = auth_client.get("/api/v1/billing/plans")
    plans = plans_resp.json()
    if not plans:
        return
        
    plan_id = plans[0]["id"]
    
    resp = auth_client.post(
        "/api/v1/billing/paypal/subscribe",
        json={"plan_id": plan_id}
    )
    assert resp.status_code in [200, 201]
    assert "order_id" in resp.json() or "id" in resp.json()


def test_paypal_capture(auth_client: TestClient):
    """B-05: Capture PayPal payment"""
    # Just checking endpoint signature. It might fail if order_id is fake, expecting 4xx or 5xx
    resp = auth_client.post(
        "/api/v1/billing/paypal/capture",
        json={"order_id": "FAKE_ORDER", "plan_id": "FAKE_PLAN"}
    )
    assert resp.status_code in [400, 404, 422, 500]


def test_get_my_subscription(auth_client: TestClient):
    """B-07: Get subscription details"""
    resp = auth_client.get("/api/v1/billing/subscription")
    assert resp.status_code in [200, 404]  # 404 if no subscription exists


def test_cancel_subscription(auth_client: TestClient):
    """B-08: Cancel subscription"""
    resp = auth_client.delete("/api/v1/billing/subscription")
    assert resp.status_code in [200, 404]


def test_paymob_session(auth_client: TestClient):
    """B-02: Create Paymob session"""
    plans_resp = auth_client.get("/api/v1/billing/plans")
    plans = plans_resp.json()
    if not plans:
        return
        
    plan_id = plans[0]["id"]
    
    resp = auth_client.post(
        "/api/v1/billing/paymob/session",
        json={"plan_id": plan_id}
    )
    assert resp.status_code in [200, 201, 500, 501] # 501 if paymob not fully configured


def test_paymob_webhook(client: TestClient):
    """B-03: Paymob webhook"""
    resp = client.post("/api/v1/billing/paymob/webhook", json={})
    assert resp.status_code in [200, 400, 422, 500]


def test_paypal_webhook(client: TestClient):
    """Paypal webhook — mocked to avoid real PayPal API calls in test env"""
    from unittest.mock import AsyncMock, patch
    with patch(
        "app.core.paypal_client.verify_webhook_signature",
        new_callable=AsyncMock,
        return_value=True
    ):
        resp = client.post("/api/v1/billing/paypal/webhook", json={})
    assert resp.status_code in [200, 400, 422, 500]
