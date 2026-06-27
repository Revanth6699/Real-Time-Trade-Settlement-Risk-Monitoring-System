import json
import redis.asyncio as redis

from fastapi import APIRouter
from fastapi import WebSocket

router = APIRouter()

ALERT_CHANNEL = "alerts_channel"


@router.websocket("/ws/alerts")
async def alerts_socket(websocket: WebSocket):

    await websocket.accept()

    redis_client = redis.Redis(
        host="redis",
        port=6379,
        decode_responses=True
    )

    pubsub = redis_client.pubsub()

    await pubsub.subscribe(ALERT_CHANNEL)

    while True:

        message = await pubsub.get_message(
            ignore_subscribe_messages=True,
            timeout=1.0
        )

        if message:

            await websocket.send_json(
                json.loads(message["data"])
            )