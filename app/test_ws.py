import asyncio
import websockets

async def listen():

    uri = "ws://localhost:8000/ws/trades"

    async with websockets.connect(uri) as websocket:

        await websocket.send("connect")

        while True:

            message = await websocket.recv()

            print(message)

asyncio.run(listen())