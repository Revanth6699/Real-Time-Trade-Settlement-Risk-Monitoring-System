import redis
import os

redis_client = redis.from_url(
    os.getenv("REDIS_URL"),
    decode_responses=True
)

def increment(metric: str, amount: int = 1):
    redis_client.incrby(metric, amount)

def set_value(metric: str, value):
    redis_client.set(metric, value)

def get_value(metric: str):
    value = redis_client.get(metric)
    return float(value) if value else 0