import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.deps import get_current_user
from app.models.user import User, UserRole
import uuid


def make_fake_user():
    return User(
        id=uuid.uuid4(),
        name="Test",
        email="t@t.com",
        google_id="g1",
        role=UserRole.student,
        is_active=True,
    )


@pytest.mark.asyncio
async def test_get_me_unauthorized():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/users/me")
    assert resp.status_code in (401, 403)  # no bearer header


@pytest.mark.asyncio
async def test_get_me_with_fake_user():
    fake_user = make_fake_user()
    app.dependency_overrides[get_current_user] = lambda: fake_user
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/users/me", headers={"Authorization": "Bearer fake"})
        assert resp.status_code == 200
        assert resp.json()["email"] == "t@t.com"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
