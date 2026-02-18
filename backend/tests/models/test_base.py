import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.models.base import Base


@pytest.mark.asyncio
async def test_engine_connects():
    from app.core.database import engine
    async with engine.begin() as conn:
        result = await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        assert result.scalar() == 1
