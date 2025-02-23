import asyncio
import json
import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class WebSocketService:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.symbol_subscribers: Dict[str, Set[str]] = {}

    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = set()
        self.active_connections[client_id].add(websocket)
        logger.info(f"Client {client_id} connected")

    async def subscribe_to_symbol(self, client_id: str, symbol: str):
        if symbol not in self.symbol_subscribers:
            self.symbol_subscribers[symbol] = set()
        self.symbol_subscribers[symbol].add(client_id)
        logger.info(f"Client {client_id} subscribed to {symbol}")

    async def broadcast_price_update(self, symbol: str, price_data: dict):
        if symbol in self.symbol_subscribers:
            message = json.dumps({
                "type": "price_update",
                "symbol": symbol,
                "data": price_data
            })
            for client_id in self.symbol_subscribers[symbol]:
                if client_id in self.active_connections:
                    websockets = self.active_connections[client_id]
                    for websocket in websockets:
                        try:
                            await websocket.send_text(message)
                        except Exception as e:
                            logger.error(f"Error sending to client {client_id}: {e}")
                            await self.disconnect(client_id, websocket)

    async def broadcast_signal(self, signal_data: dict):
        message = json.dumps({
            "type": "trading_signal",
            "data": signal_data
        })
        for websockets in self.active_connections.values():
            for websocket in websockets:
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    logger.error(f"Error broadcasting signal: {e}")

    async def disconnect(self, client_id: str, websocket: WebSocket):
        try:
            if client_id in self.active_connections:
                self.active_connections[client_id].remove(websocket)
                if not self.active_connections[client_id]:
                    del self.active_connections[client_id]

            # Sembol aboneliklerini temizle
            for symbol in list(self.symbol_subscribers.keys()):
                if client_id in self.symbol_subscribers[symbol]:
                    self.symbol_subscribers[symbol].remove(client_id)
                    if not self.symbol_subscribers[symbol]:
                        del self.symbol_subscribers[symbol]

            logger.info(f"Client {client_id} disconnected")
        except Exception as e:
            logger.error(f"Error during disconnect for client {client_id}: {e}")
