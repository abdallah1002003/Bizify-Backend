"""
Google OAuth2 client.
Handles exchanging authorization codes for tokens and fetching user info.
"""
import httpx

from app.core.config import settings

# Google OAuth endpoints
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


def get_google_auth_url(redirect_uri: str) -> str:
    """
    Constructs the URL that the frontend/user should visit to initiate Google Login.
    """
    client_id = settings.GOOGLE_CLIENT_ID
    return (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"response_type=code&"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"scope=openid%20email%20profile&"
        f"access_type=offline&"
        f"prompt=consent"
    )


async def exchange_code_for_token(code: str, redirect_uri: str) -> str:
    """
    Exchanges the Authorization Code for an Access Token.
    """
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(GOOGLE_TOKEN_URL, data=data)
        response.raise_for_status()
        return response.json().get("access_token")


async def get_google_user_info(access_token: str) -> dict:
    """
    Uses the Access Token to fetch the user's profile info from Google.
    Returns a dictionary containing 'email', 'name', 'picture', etc.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(GOOGLE_USERINFO_URL, headers=headers)
        response.raise_for_status()
        return response.json()
