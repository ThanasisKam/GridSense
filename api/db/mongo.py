import os
from motor.motor_asyncio import AsyncIOMotorClient

_client = None
_db = None


async def connect() -> None:
    global _client, _db
    uri = os.getenv("MONGO_URI", "mongodb://gridsense:gridsense_dev_pass@catalog-db:27017")
    _client = AsyncIOMotorClient(uri)
    _db = _client["gridsense"]
    # Verify connection
    await _client.admin.command("ping")
    print("MongoDB connected.")


async def disconnect() -> None:
    global _client
    if _client:
        _client.close()


def get_db():
    if _db is None:
        raise RuntimeError("MongoDB not initialised.")
    return _db