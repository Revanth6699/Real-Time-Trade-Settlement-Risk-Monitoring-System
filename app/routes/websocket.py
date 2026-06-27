import json
import redis.asyncio as redis

from fastapi import APIRouter
from fastapi import WebSocket
from fastapi import WebSocketDisconnect

from app.websocket_manager import manager

router = APIRouter()

REDIS_HOST = "redis"
REDIS_PORT = 6379

CHANNEL = "trades_channel"


@router.websocket("/ws/trades")
async def websocket_endpoint(websocket: WebSocket):

    await manager.connect(websocket)

    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True
    )

    pubsub = redis_client.pubsub()

    await pubsub.subscribe(CHANNEL)

    try:

        while True:

            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=1.0
            )

            if message:

                trade_data = json.loads(
                    message["data"]
                )

                await websocket.send_json(
                    trade_data
                )

    except WebSocketDisconnect:

        manager.disconnect(websocket)

    finally:

        await pubsub.unsubscribe(CHANNEL)

        await pubsub.close()

        await redis_client.close()