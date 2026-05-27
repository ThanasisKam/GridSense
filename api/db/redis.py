import os
import redis.asyncio as aioredis

_client = None


async def connect() -> None:
    global _client
    url = os.getenv("REDIS_URL", "redis://:gridsense_dev_pass@cache:6379/0")
    _client = aioredis.from_url(url, decode_responses=True)
    await _client.ping()
    print("Redis connected.")


async def disconnect() -> None:
    global _client
    if _client:
        await _client.aclose()


def get_client() -> aioredis.Redis:
    if _client is None:
        raise RuntimeError("Redis client not initialised.")
    return _client