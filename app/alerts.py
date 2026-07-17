import json
import redis.asyncio as redis
import os

REDIS_URL = os.getenv("REDIS_URL")

redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True
)
ALERT_CHANNEL = "alerts_channel"


async def publish_alert(alert_data: dict):


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