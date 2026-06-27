from fastapi import WebSocket

class ConnectionManager:

    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket):
        await websocket.accept()
        self.active_connections.append(websocket)

        print(
            "WebSocket Connected:",
            len(self.active_connections)
        )
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)



    
    async def broadcast(self, message):

        dead = []
        
        print("Broadcasting to:",len(self.active_connections))

        for connection in self.active_connections:

            try:
                await connection.send_json(message)

            except Exception:
                dead.append(connection)

        for conn in dead:
            self.disconnect(conn)

manager = ConnectionManager()