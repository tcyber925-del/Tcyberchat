import httpx
from urllib.parse import urlencode
from ..core.config import settings

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

def get_google_auth_url():
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

async def get_google_user_info(code: str):
    async with httpx.AsyncClient() as client:
        # Exchange code for token
        token_data = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        }
        
        token_res = await client.post(GOOGLE_TOKEN_URL, data=token_data)
        if token_res.status_code != 200:
            return None, f"Failed to get token: {token_res.text}"
            
        access_token = token_res.json().get("access_token")
        
        # Get user info
        user_res = await client.get(
            GOOGLE_USERINFO_URL, 
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if user_res.status_code != 200:
            return None, "Failed to get user info"
            
        return user_res.json(), None
