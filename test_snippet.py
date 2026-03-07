import asyncio
from unittest.mock import AsyncMock, MagicMock

async def test_db():
    db = MagicMock()
    mock_transaction = MagicMock()
    # To mock async with db.begin():
    mock_transaction.__aenter__ = AsyncMock(return_value=mock_transaction)
    mock_transaction.__aexit__ = AsyncMock(return_value=None)
    db.begin.return_value = mock_transaction
    
    try:
        async with db.begin():
            print("db.begin() SUCCESS")
    except Exception as e:
        print("db.begin() FAILED", e)

asyncio.run(test_db())
