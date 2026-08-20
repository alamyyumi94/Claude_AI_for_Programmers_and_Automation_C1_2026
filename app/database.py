from typing import Any
from pymongo import AsyncMongoClient
from app.config import get_settings

_client: AsyncMongoClient | None = None
_database: Any | None = None


async def connect_to_database() -> Any:
    global _client, _database  # Connect onece at app startup
    if _client is None:
        settings = get_settings()
        _client = AsyncMongoClient(settings.mongodb_uri.get_secret_value().strip())
        _database = _client[settings.mongodb_database]
        try:
            # Test the connection
            await _client.admin.command("ping")
        except Exception as e:
            await close_database_connection()
            raise RuntimeError(f"Failed to connect to MongoDB: {e}")
    return _database


def get_database() -> Any:
    if _database is None:
        raise RuntimeError(
            "Database connection is not established. Call connect_to_database() first."
        )
    return _database


async def close_database_connection() -> None:
    global _client, _database
    if _client is not None:
        await _client.close()
        _client = None
        _database = None
