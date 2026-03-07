import asyncio
from unittest.mock import AsyncMock, MagicMock

# The problem is `__aenter__` doesn't work if db.begin() returns a `MagicMock`.
# It needs to return an `AsyncMock`.
async def test_db():
    db = AsyncMock()
    mock_transaction = AsyncMock()
    # To mock async with db.begin():
    mock_transaction.__aenter__.return_value = mock_transaction
    mock_transaction.__aexit__.return_value = None
    db.begin.return_value = mock_transaction
    
    try:
        async with db.begin():
            print("db.begin() SUCCESS")
    except Exception as e:
        print("db.begin() FAILED", e)

asyncio.run(test_db())
