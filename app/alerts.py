import json
import redis.asyncio as redis

REDIS_HOST = "redis"
REDIS_PORT = 6379

ALERT_CHANNEL = "alerts_channel"


async def publish_alert(alert_data: dict):

    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True
    )

    await redis_client.publish(
        ALERT_CHANNEL,
        json.dumps(alert_data)
    )

    await redis_client.close()

def check_alerts(trade):

    alerts = []

    if trade["risk_score"] > 80:
        alerts.append("HIGH RISK TRADE")

    if trade["settlement_status"] == "FAILED":
        alerts.append("FAILED TRADE")

    if trade["anomaly_flag"]:
        alerts.append("ANOMALY DETECTED")

    return alerts