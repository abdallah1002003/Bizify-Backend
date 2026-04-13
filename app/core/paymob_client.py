"""
Paymob payment gateway client.

Implements Paymob's three-step card payment flow:
  1. Authentication  → obtain a short-lived API token.
  2. Order registration → register the order in Paymob's system.
  3. Payment key generation → exchange for a single-use iframe token.

Also provides HMAC validation for Transaction Processed callbacks.
"""
import hashlib
import hmac
from decimal import Decimal
from typing import Any, Dict

import httpx

from app.core.config import settings

PAYMOB_BASE_URL = "https://accept.paymob.com/api"


async def _authenticate() -> str:
    """
    Step 1 – Authenticate with Paymob and return a short-lived API token.
    Raises httpx.HTTPStatusError on failure.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYMOB_BASE_URL}/auth/tokens",
            json={"api_key": settings.PAYMOB_API_KEY},
        )
        response.raise_for_status()
        return response.json()["token"]


async def _register_order(
    auth_token: str,
    amount_cents: int,
    currency: str,
    merchant_order_id: str,
) -> Dict[str, Any]:
    """
    Step 2 – Register an order in Paymob.
    Returns the full Paymob order object (includes Paymob's numeric order ID).

    Args:
        auth_token:        Token from _authenticate().
        amount_cents:      Amount in the smallest currency unit (e.g. 1099 → 10.99 EGP).
        currency:          ISO 4217 code (e.g. "EGP").
        merchant_order_id: Our internal identifier for reconciliation (usually plan UUID).
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYMOB_BASE_URL}/ecommerce/orders",
            json={
                "auth_token": auth_token,
                "delivery_needed": False,
                "amount_cents": amount_cents,
                "currency": currency,
                "merchant_order_id": merchant_order_id,
                "items": [],
            },
        )
        response.raise_for_status()
        return response.json()


async def _get_payment_key(
    auth_token: str,
    paymob_order_id: int,
    amount_cents: int,
    currency: str,
    billing_data: Dict[str, str],
) -> str:
    """
    Step 3 – Generate a single-use payment key that the frontend embeds in the iframe URL.

    Args:
        auth_token:       Token from _authenticate().
        paymob_order_id:  Numeric order ID returned from _register_order().
        amount_cents:     Must match the order amount exactly.
        currency:         ISO 4217 code.
        billing_data:     Minimal billing dict required by Paymob.
    Returns:
        A payment token string (valid for a limited time).
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYMOB_BASE_URL}/acceptance/payment_keys",
            json={
                "auth_token": auth_token,
                "amount_cents": amount_cents,
                "expiration": 3600,
                "order_id": paymob_order_id,
                "billing_data": billing_data,
                "currency": currency,
                "integration_id": settings.PAYMOB_INTEGRATION_ID,
            },
        )
        response.raise_for_status()
        return response.json()["token"]


async def create_card_payment(
    amount: Decimal,
    currency: str,
    merchant_order_id: str,
    billing_data: Dict[str, str],
) -> Dict[str, Any]:
    """
    High-level helper that executes the full 3-step Paymob flow and returns
    the iframe URL and Paymob's order ID for storage.

    Args:
        amount:            Payment amount as a Decimal (e.g. Decimal("49.99")).
        currency:          ISO 4217 code (e.g. "EGP").
        merchant_order_id: Internal reference – usually the subscription plan UUID.
        billing_data:      Billing details for the cardholder (name, email, phone, …).

    Returns:
        {
            "iframe_url":       Full URL to render in front-end iframe.
            "paymob_order_id":  Paymob's numeric order ID (stored on Payment record).
        }
    """
    amount_cents = int(amount * 100)

    auth_token = await _authenticate()

    order_data = await _register_order(
        auth_token=auth_token,
        amount_cents=amount_cents,
        currency=currency,
        merchant_order_id=merchant_order_id,
    )
    paymob_order_id: int = order_data["id"]

    payment_token = await _get_payment_key(
        auth_token=auth_token,
        paymob_order_id=paymob_order_id,
        amount_cents=amount_cents,
        currency=currency,
        billing_data=billing_data,
    )

    iframe_url = (
        f"https://accept.paymob.com/api/acceptance/iframes/"
        f"{settings.PAYMOB_IFRAME_ID}?payment_token={payment_token}"
    )

    return {
        "iframe_url": iframe_url,
        "paymob_order_id": str(paymob_order_id),
    }


def verify_hmac(data: Dict[str, Any]) -> bool:
    """
    Validates the HMAC signature sent by Paymob in the Transaction Processed callback.

    Paymob concatenates specific transaction fields in a defined order,
    then signs them with the HMAC secret using SHA-512.

    Args:
        data: The full JSON body received from Paymob's callback.

    Returns:
        True if the HMAC is valid, False otherwise.
    """
    hmac_secret = settings.PAYMOB_HMAC_SECRET
    if not hmac_secret:
        return False

    received_hmac = data.get("hmac", "")

    # Paymob-defined concatenation order
    obj = data.get("obj", {})
    fields = [
        str(obj.get("amount_cents", "")),
        str(obj.get("created_at", "")),
        str(obj.get("currency", "")),
        str(obj.get("error_occured", "")),
        str(obj.get("has_parent_transaction", "")),
        str(obj.get("id", "")),
        str(obj.get("integration_id", "")),
        str(obj.get("is_3d_secure", "")),
        str(obj.get("is_auth", "")),
        str(obj.get("is_capture", "")),
        str(obj.get("is_refunded", "")),
        str(obj.get("is_standalone_payment", "")),
        str(obj.get("is_voided", "")),
        str(obj.get("order", {}).get("id", "")),
        str(obj.get("owner", "")),
        str(obj.get("pending", "")),
        str(obj.get("source_data", {}).get("pan", "")),
        str(obj.get("source_data", {}).get("sub_type", "")),
        str(obj.get("source_data", {}).get("type", "")),
        str(obj.get("success", "")),
    ]

    concatenated = "".join(fields)

    expected_hmac = hmac.new(
        hmac_secret.encode("utf-8"),
        concatenated.encode("utf-8"),
        hashlib.sha512,
    ).hexdigest()

    return hmac.compare_digest(expected_hmac, received_hmac)
