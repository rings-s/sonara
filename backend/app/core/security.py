from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import httpx
from app.core.config import settings

ALGORITHM = "HS256"
GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": user_id, "exp": expire}, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """Returns user_id string or None if invalid."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


async def verify_google_token(id_token: str) -> dict | None:
    """
    Verify Google ID token and return user info dict, or None if invalid.
    Returns: {"sub": google_id, "email": ..., "name": ..., "picture": ...}
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(GOOGLE_TOKEN_INFO_URL, params={"id_token": id_token})
        if resp.status_code != 200:
            return None
        data = resp.json()
        if data.get("aud") != settings.GOOGLE_CLIENT_ID:
            return None
        return data
