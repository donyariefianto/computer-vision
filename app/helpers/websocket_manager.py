import asyncio
from typing import Dict

from fastapi import WebSocket

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session: str):
        """Menambahkan koneksi WebSocket baru"""
        await websocket.accept()
        self.active_connections[session] = websocket

    def disconnect(self, session: str):
        """Menghapus koneksi WebSocket ketika terputus"""
        self.active_connections.pop(session, None)

    async def send_personal_message(self, message: str, session: str):
        """Mengirim pesan ke sesi tertentu"""
        if session in self.active_connections:
            await self.active_connections[session].send_json({"message": message})

    async def broadcast(self, message: str):
        """Mengirim pesan ke semua sesi yang terhubung"""
        for ws in self.active_connections.values():
            await ws.send_text(f"[Broadcast] {message}")

websocket_manager = WebSocketManager()