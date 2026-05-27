from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from db.cassandra import get_session
from db.redis import get_client
from models.cassandra import SensorReadingIn, SensorReadingOut

router = APIRouter(prefix="/sensors", tags=["Sensors (Cassandra)"])


def _bucket(dt: datetime) -> str:
    """Hour-level bucket string: YYYYMMDDHH — caps partition size."""
    return dt.strftime("%Y%m%d%H")


def _minute_bucket(dt: datetime) -> str:
    """Minute-level bucket for dashboard table."""
    return dt.strftime("%Y%m%d%H%M")


@router.post("/readings", status_code=201)
async def ingest_readings(readings: List[SensorReadingIn]):
    """
    Ingest one or a batch of sensor readings.
    Writes to BOTH tables (sensor_readings + sensor_readings_by_time).
    This write amplification is the explicit cost of the query-driven design.
    """
    session = get_session()
    now = datetime.now(timezone.utc)
    bucket = _bucket(now)
    time_bucket = _minute_bucket(now)

    insert_main = session.prepare("""
        INSERT INTO sensor_readings
            (sensor_id, bucket, reading_time, metric_type, value, unit, quality_flag)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """)
    insert_dashboard = session.prepare("""
        INSERT INTO sensor_readings_by_time
            (time_bucket, reading_time, sensor_id, metric_type, value, unit, quality_flag)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """)

    for r in readings:
        session.execute(insert_main, (r.sensor_id, bucket, now, r.metric_type, r.value, r.unit, r.quality_flag))
        session.execute(insert_dashboard, (time_bucket, now, r.sensor_id, r.metric_type, r.value, r.unit, r.quality_flag))

        # Invalidate Redis cache for this sensor so next /summary is fresh
        redis = get_client()
        await redis.delete(f"sensor:summary:{r.sensor_id}")

    return {"ingested": len(readings), "bucket": bucket}


@router.get("/{sensor_id}/readings", response_model=List[SensorReadingOut])
async def get_readings(
    sensor_id: str,
    limit: int = Query(default=20, le=1000),
    from_time: Optional[datetime] = None,
):
    """
    Last N readings for a sensor, optionally filtered by start time.
    Queries sensor_readings — optimised for this access pattern (partition per sensor+hour).
    """
    session = get_session()

    if from_time:
        # Need to query across potentially multiple buckets
        rows = session.execute("""
            SELECT sensor_id, reading_time, metric_type, value, unit, quality_flag
            FROM sensor_readings
            WHERE sensor_id = %s AND bucket = %s AND reading_time >= %s
            LIMIT %s
        """, (sensor_id, _bucket(from_time), from_time, limit))
    else:
        # Most recent bucket only — fastest path
        now = datetime.now(timezone.utc)
        rows = session.execute("""
            SELECT sensor_id, reading_time, metric_type, value, unit, quality_flag
            FROM sensor_readings
            WHERE sensor_id = %s AND bucket = %s
            LIMIT %s
        """, (sensor_id, _bucket(now), limit))

    result = [SensorReadingOut(**dict(row._asdict())) for row in rows]
    if not result:
        raise HTTPException(status_code=404, detail=f"No readings found for sensor '{sensor_id}'")
    return result


@router.get("/{sensor_id}/summary")
async def get_summary(sensor_id: str):
    """
    Cached summary for a sensor: latest value + last-hour stats.
    Redis TTL = 30 seconds. Cache miss falls through to Cassandra.
    """
    redis = get_client()
    cache_key = f"sensor:summary:{sensor_id}"

    cached = await redis.get(cache_key)
    if cached:
        import json
        return {"source": "cache", "data": json.loads(cached)}

    # Cache miss — query Cassandra
    session = get_session()
    now = datetime.now(timezone.utc)
    rows = list(session.execute("""
        SELECT sensor_id, reading_time, metric_type, value, unit, quality_flag
        FROM sensor_readings
        WHERE sensor_id = %s AND bucket = %s
        LIMIT 100
    """, (sensor_id, _bucket(now))))

    if not rows:
        raise HTTPException(status_code=404, detail=f"No data for sensor '{sensor_id}'")

    values = [r.value for r in rows]
    summary = {
        "sensor_id": sensor_id,
        "latest_value": rows[0].value,
        "latest_time": rows[0].reading_time.isoformat(),
        "metric_type": rows[0].metric_type,
        "unit": rows[0].unit,
        "count_1h": len(values),
        "avg_1h": round(sum(values) / len(values), 4),
        "min_1h": min(values),
        "max_1h": max(values),
    }

    import json
    await redis.setex(cache_key, 30, json.dumps(summary))
    return {"source": "cassandra", "data": summary}