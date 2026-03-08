import asyncio
from unittest.mock import AsyncMock, MagicMock

async def test_db():
    db = AsyncMock()
    mock_transaction = MagicMock()
    mock_transaction.__aenter__ = AsyncMock(return_value=mock_transaction)
    mock_transaction.__aexit__ = AsyncMock(return_value=None)
    # The key is giving it a normal property that is not a mock function returning a coroutine
    # If db.begin is AsyncMock, db.begin() returns a coroutine.
    # So db.begin cannot be an AsyncMock.
    db.begin = MagicMock(return_value=mock_transaction)
    
    try:
        async with db.begin():
            print("db.begin() SUCCESS")
    except Exception as e:
        print("db.begin() FAILED", e)

asyncio.run(test_db())
