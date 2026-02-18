import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from app.main import app


@pytest.mark.asyncio
async def test_google_login_invalid_token():
    with patch("app.api.v1.routes.auth.verify_google_token", new_callable=AsyncMock, return_value=None):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/google", json={"id_token": "bad_token"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_google_login_creates_user(monkeypatch):
    import uuid
    fake_user_info = {
        "sub": f"google_{uuid.uuid4().hex}",
        "email": f"test_{uuid.uuid4().hex}@example.com",
        "name": "Test User",
        "picture": None,
    }
    with patch("app.api.v1.routes.auth.verify_google_token", new_callable=AsyncMock, return_value=fake_user_info):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/google", json={"id_token": "valid"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()
