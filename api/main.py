from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI

import db.cassandra as cassandra_db
import db.neo4j as neo4j_db
import db.mongo as mongo_db
import db.postgres as postgres_db
import db.redis as redis_db

from routers import sensors, grid, equipment, billing, alerts


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan: runs on startup (before yield) and shutdown (after yield).
    All database connections are opened here and stored globally in each db module.
    Cassandra uses a synchronous driver so it runs in a thread pool executor.
    """
    print("GridSense API starting — connecting to databases...")

    # Cassandra blocks (synchronous driver) — run in thread pool
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, cassandra_db.connect)

    # Async drivers connect natively
    await neo4j_db.connect()
    await mongo_db.connect()
    await postgres_db.connect()
    await redis_db.connect()

    print("All database connections established. GridSense API ready.")
    yield

    # Graceful shutdown
    await neo4j_db.disconnect()
    await mongo_db.disconnect()
    await postgres_db.disconnect()
    await redis_db.disconnect()
    print("GridSense API shut down.")


app = FastAPI(
    title="GridSense API",
    description=(
        "Smart Power Grid Analytics & Fault Management Platform. "
        "Polyglot persistence: Cassandra · Neo4j · MongoDB · PostgreSQL · Redis."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(sensors.router)
app.include_router(grid.router)
app.include_router(equipment.router)
app.include_router(billing.router)
app.include_router(alerts.router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "GridSense API",
        "version": "1.0.0",
        "status": "ok",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    """Quick health check — used by Docker and monitoring."""
    return {"status": "ok"}