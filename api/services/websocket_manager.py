import asyncio
import json
import logging
from typing import Dict, List

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            f"Client {client_id} connected. Total connections: {len(self.active_connections)}"
        )

    async def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        # Remove from all subscriptions
        for symbol in self.subscriptions:
            if websocket in self.subscriptions[symbol]:
                self.subscriptions[symbol].remove(websocket)

    async def subscribe_to_symbol(self, websocket: WebSocket, symbol: str):
        if symbol not in self.subscriptions:
            self.subscriptions[symbol] = []
        self.subscriptions[symbol].append(websocket)
        logger.info(f"Client subscribed to {symbol}")

    async def broadcast_update(self, symbol: str, data: dict):
        if symbol in self.subscriptions:
            dead_connections = []
            for connection in self.subscriptions[symbol]:
                try:
                    await connection.send_json(data)
                except Exception as e:
                    logger.error(f"Failed to send update: {e}")
                    dead_connections.append(connection)

            # Cleanup dead connections
            for dead in dead_connections:
                await self.disconnect(dead)
