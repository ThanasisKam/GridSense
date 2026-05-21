import os
from neo4j import AsyncGraphDatabase

_driver = None


async def connect() -> None:
    global _driver
    uri = os.getenv("NEO4J_URI", "bolt://graph-db:7687")
    password = os.getenv("NEO4J_PASSWORD", "gridsense_dev_pass")
    _driver = AsyncGraphDatabase.driver(uri, auth=("neo4j", password))
    await _driver.verify_connectivity()
    print("Neo4j connected.")


async def disconnect() -> None:
    global _driver
    if _driver:
        await _driver.close()


def get_driver():
    if _driver is None:
        raise RuntimeError("Neo4j driver not initialised.")
    return _driver