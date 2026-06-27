import json
import redis

REDIS_HOST = "redis"
REDIS_PORT = 6379

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)

CHANNEL = "trades_channel"

def publish_trade(trade_data: dict):

    redis_client.publish(
        CHANNEL,
        json.dumps(trade_data)
    )