import os
import asyncpg

_pool = None


async def connect() -> None:
    global _pool
    dsn = os.getenv("POSTGRES_DSN", "postgresql://gridsense:gridsense_dev_pass@billing-db:5432/gridsense")
    _pool = await asyncpg.create_pool(dsn, min_size=2, max_size=10)
    print("PostgreSQL connected.")


async def disconnect() -> None:
    global _pool
    if _pool:
        await _pool.close()


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("PostgreSQL pool not initialised.")
    return _pool