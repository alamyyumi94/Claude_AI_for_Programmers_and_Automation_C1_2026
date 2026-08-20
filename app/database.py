from typing import Any

from pymongo import AsyncMongoClient

from app.config import get_settings

# Shared MongoDB client instance
_client: AsyncMongoClient | None = None
_database: Any | None = None

async def connect_to_database() -> None:
    global _client, _database   # Connect once at app startup
    if _client is not None:
        return  # Already connected
    
    settings = get_settings()

    client = AsyncMongoClient(
        settings.mongodb_uri.get_secret_value()
    )

    try:
        # Test the connection by pinging the server
        await client.admin.command("ping")
    except Exception:
        await client.close()
        raise

    _client = client
    _database = client[settings.mongodb_database]

def get_database() -> Any:
    if _database is None:
        raise RuntimeError("Database connection is not established. Call connect_to_database() first.")
    return _database

async def close_database() -> None:
    global _client, _database
    if _client is not None:
        await _client.close()

        # Clear references so later startup begins from a clean slate
        _client = None
        _database = None
