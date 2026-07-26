from fastapi import WebSocket
from typing import Dict


class ConnectionManager:
    def __init__(self):
        # user_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        self.device_tokens: Dict[str, str] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, user_id: str, message: dict):
        websocket = self.active_connections.get(user_id)
        if websocket:
            await websocket.send_json(message)

    def register_device_token(self, user_id: str, token: str):
        self.device_tokens[user_id] = token

    def get_device_token(self, user_id: str) -> str | None:
        return self.device_tokens.get(user_id)

    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)


manager = ConnectionManager()