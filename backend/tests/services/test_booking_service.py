import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.booking_service import calculate_price
import uuid


@pytest.mark.asyncio
async def test_calculate_price_no_teacher():
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=mock_result)
    price = await calculate_price(uuid.uuid4(), 60, db)
    assert price == 0.0
