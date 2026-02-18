import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.models.base import Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"
