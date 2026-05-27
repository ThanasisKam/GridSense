import json
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db.redis import get_client

router = APIRouter(prefix="/alerts", tags=["Alerts (Redis)"])

ALERT_CHANNEL = "gridsense:fault_alerts"
ACTIVE_ALERTS_KEY = "gridsense:active_alerts"


class AlertIn(BaseModel):
    node_id: str
    severity: str       # info | warning | critical
    message: str


@router.post("/publish", status_code=201)
async def publish_alert(alert: AlertIn):
    """
    Publish a fault alert to the Redis Pub/Sub channel.
    Also stores it in a Redis list so GET /alerts/active can read recent alerts
    even if the subscriber was offline during the publish.
    """
    redis = get_client()
    payload = {
        "node_id": alert.node_id,
        "severity": alert.severity,
        "message": alert.message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    serialised = json.dumps(payload)

    # Pub/Sub — real-time delivery to subscribed dashboards
    await redis.publish(ALERT_CHANNEL, serialised)

    # Also push to a capped list (last 100 alerts) for REST polling
    await redis.lpush(ACTIVE_ALERTS_KEY, serialised)
    await redis.ltrim(ACTIVE_ALERTS_KEY, 0, 99)
    # TTL: alerts auto-expire after 24 hours
    await redis.expire(ACTIVE_ALERTS_KEY, 86400)

    return {"published": True, "channel": ALERT_CHANNEL, "alert": payload}


@router.get("/active")
async def get_active_alerts():
    """
    Return the most recent fault alerts stored in Redis.
    This is the REST-polling companion to the Pub/Sub channel.
    """
    redis = get_client()
    raw_alerts = await redis.lrange(ACTIVE_ALERTS_KEY, 0, 99)
    alerts = [json.loads(a) for a in raw_alerts]
    return {"count": len(alerts), "alerts": alerts}