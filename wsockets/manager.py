import uuid
from fastapi import WebSocket
from typing import Dict, Optional

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, dict] = {}

    def validate_token(self, token: str) -> bool:
        return token == "MY_SECRET_TOKEN565" #Placeholder

    async def connect(self, websocket: WebSocket) -> str:
        await websocket.accept()
        client_id = str(uuid.uuid4())
        self.active_connections[client_id] = {
            "websocket": websocket,
        }
        return client_id

    def disconnect(self, client_id: str, code: Optional[int] = None):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            if code == 1006 or code == 1015:
                print(f"Reconnecting client {client_id} due to unexpected disconnection (code: {code})")
                

    def get_client(self, client_id: str) -> Optional[dict]:
        return self.active_connections.get(client_id)

    def get_websocket(self, client_id: str) -> Optional[WebSocket]:
        client = self.get_client(client_id)
        return client["websocket"] if client else None

    def is_authenticated(self, client_id: str) -> bool:
        client = self.get_client(client_id)
        return client["authenticated"] if client else False

    def get_all_client_ids(self) -> list[str]:
        return list(self.active_connections.keys())

    def get_authenticated_clients(self) -> list[str]:
        return [
            client_id for client_id, client in self.active_connections.items()
            if client["authenticated"]
        ]
    
    async def send_message(self, message: str, client_id: str):
        websocket = self.get_websocket(client_id)
        if websocket:
            await websocket.send_text(message)

    async def send_json(self, data: dict, client_id: str):
        websocket = self.get_websocket(client_id)
        if websocket:
            await websocket.send_json(data)

    async def broadcast(self, message: str, authenticated_only: bool = False):
        client_ids = self.get_authenticated_clients() if authenticated_only else self.get_all_client_ids()
        for client_id in client_ids:
            websocket = self.get_websocket(client_id)
            if websocket:
                await websocket.send_text(message)

    async def broadcast_json(self, data: dict, authenticated_only: bool = False):
        client_ids = self.get_authenticated_clients() if authenticated_only else self.get_all_client_ids()
        for client_id in client_ids:
            websocket = self.get_websocket(client_id)
            if websocket:
                await websocket.send_json(data)

    async def ping(self, websocket: WebSocket):
        await websocket.send_json({"event": "pong"})