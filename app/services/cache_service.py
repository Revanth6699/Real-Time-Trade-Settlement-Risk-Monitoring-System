import redis
import json

redis_client = redis.Redis(
    host="redis",
    port=6379,
    decode_responses=True
)

def set_cache(key, value):
    redis_client.set(
        key,
        json.dumps(value)
    )

def get_cache(key):

    data = redis_client.get(key)

    if data:
        return json.loads(data)

    return None