"""
PayPal REST API client.
Handles authentication and core API calls using PayPal's Orders API v2.
"""
import httpx

from app.core.config import settings

# PayPal base URLs
PAYPAL_URLS = {
    "sandbox": "https://api-m.sandbox.paypal.com",
    "live":    "https://api-m.paypal.com",
}


def _base_url() -> str:
    return PAYPAL_URLS.get(settings.PAYPAL_MODE, PAYPAL_URLS["sandbox"])


async def get_access_token() -> str:
    """
    Fetches a short-lived Bearer token from PayPal using client credentials.
    """
    url = f"{_base_url()}/v1/oauth2/token"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            data={"grant_type": "client_credentials"},
            auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
        )
        response.raise_for_status()
        return response.json()["access_token"]


async def create_order(amount: str, currency: str, plan_id: str) -> dict:
    """
    Creates a PayPal Order for one-time payment (capture intent).
    Returns the full PayPal order object including the approval link.

    Args:
        amount:   String representation of the amount, e.g. "9.99"
        currency: ISO 4217 currency code, e.g. "USD"
        plan_id:  Internal plan UUID used as the custom_id for reconciliation
    """
    token = await get_access_token()
    url   = f"{_base_url()}/v2/checkout/orders"

    payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "custom_id": str(plan_id),
                "amount": {
                    "currency_code": currency,
                    "value": amount,
                },
            }
        ],
        "application_context": {
            "return_url": f"{settings.FRONTEND_URL}/billing/success",
            "cancel_url": f"{settings.FRONTEND_URL}/billing/cancel",
            "brand_name":  "Bizify",
            "user_action": "PAY_NOW",
        },
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        return response.json()


async def capture_order(order_id: str) -> dict:
    """
    Captures (finalises) a PayPal Order after the user has approved it.
    Returns the capture result containing the transaction ID.

    Args:
        order_id: PayPal Order ID returned from create_order()
    """
    token = await get_access_token()
    url   = f"{_base_url()}/v2/checkout/orders/{order_id}/capture"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers={
                "Authorization":  f"Bearer {token}",
                "Content-Type":   "application/json",
            },
        )
        response.raise_for_status()
        return response.json()


async def verify_webhook_signature(
    transmission_id:   str,
    transmission_time: str,
    cert_url:          str,
    auth_algo:         str,
    actual_signature:  str,
    webhook_body:      bytes,
) -> bool:
    """
    Asks PayPal to verify that an incoming webhook event is genuine.
    Returns True if the signature is valid.
    """
    token = await get_access_token()
    url   = f"{_base_url()}/v1/notifications/verify-webhook-signature"

    payload = {
        "auth_algo":         auth_algo,
        "cert_url":          cert_url,
        "transmission_id":   transmission_id,
        "transmission_sig":  actual_signature,
        "transmission_time": transmission_time,
        "webhook_id":        settings.PAYPAL_WEBHOOK_ID,
        "webhook_event":     webhook_body.decode("utf-8"),
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code != 200:
            return False

        return response.json().get("verification_status") == "SUCCESS"
