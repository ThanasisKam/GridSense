import os
import time
from cassandra.cluster import Cluster
from cassandra.policies import RoundRobinPolicy

_session = None

CASSANDRA_SCHEMA = """
CREATE KEYSPACE IF NOT EXISTS gridsense
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

CREATE TABLE IF NOT EXISTS gridsense.sensor_readings (
    sensor_id    TEXT,
    bucket       TEXT,
    reading_time TIMESTAMP,
    metric_type  TEXT,
    value        FLOAT,
    unit         TEXT,
    quality_flag TINYINT,
    PRIMARY KEY ((sensor_id, bucket), reading_time)
) WITH CLUSTERING ORDER BY (reading_time DESC)
  AND default_time_to_live = 7776000;

CREATE TABLE IF NOT EXISTS gridsense.sensor_readings_by_time (
    time_bucket  TEXT,
    reading_time TIMESTAMP,
    sensor_id    TEXT,
    metric_type  TEXT,
    value        FLOAT,
    unit         TEXT,
    quality_flag TINYINT,
    PRIMARY KEY ((time_bucket), reading_time, sensor_id)
) WITH CLUSTERING ORDER BY (reading_time DESC, sensor_id ASC)
  AND default_time_to_live = 7776000;

CREATE TABLE IF NOT EXISTS gridsense.relay_events (
    feeder_id    TEXT,
    event_time   TIMEUUID,
    relay_id     TEXT,
    event_type   TEXT,
    fault_type   TEXT,
    current_kA   FLOAT,
    voltage_kV   FLOAT,
    notes        TEXT,
    PRIMARY KEY ((feeder_id), event_time)
) WITH CLUSTERING ORDER BY (event_time ASC);
"""


def connect(retries: int = 15, delay: int = 10) -> None:
    global _session
    host = os.getenv("CASSANDRA_HOST", "timeseries-db")

    for attempt in range(1, retries + 1):
        try:
            cluster = Cluster(
                [host],
                load_balancing_policy=RoundRobinPolicy(),
                protocol_version=4,
            )
            _session = cluster.connect()
            # Create schema (idempotent — IF NOT EXISTS on every statement)
            for statement in CASSANDRA_SCHEMA.strip().split(";"):
                stmt = statement.strip()
                if stmt:
                    _session.execute(stmt)
            # Switch default keyspace
            _session.set_keyspace("gridsense")
            print("Cassandra connected and schema applied.")
            return
        except Exception as exc:
            print(f"Cassandra attempt {attempt}/{retries} failed: {exc}")
            if attempt < retries:
                time.sleep(delay)

    raise RuntimeError("Could not connect to Cassandra after retries.")


def get_session():
    if _session is None:
        raise RuntimeError("Cassandra session not initialised.")
    return _session