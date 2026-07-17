import os
import json
import redis
from dotenv import load_dotenv

load_dotenv()

redis_client = redis.Redis.from_url(
    os.getenv("REDIS_URL"),
    decode_responses=True,
)

# Verify Redis connection
try:
    redis_client.ping()
    print("Connected to Upstash Redis")
except Exception as e:
    print(f"Redis connection failed: {e}")
    redis_client = None


def set_cache(key, value):
    if redis_client is None:
        return

    try:
        redis_client.set(key, json.dumps(value))
    except Exception as e:
        print(f"Redis SET failed: {e}")

def get_cache(key):
    if redis_client is None:
        return None

    try:
        data = redis_client.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        print(f"Redis GET failed: {e}")

    return None