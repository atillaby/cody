import asyncio
import logging
from datetime import datetime
from typing import Dict

from api.services.strategy_service import StrategyService
from api.services.websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)


class SignalService:
    def __init__(self, strategy_service: StrategyService, ws_manager: WebSocketManager):
        self.strategy_service = strategy_service
        self.ws_manager = ws_manager
        self.active_symbols = ["BTC/USDT", "ETH/USDT"]  # Aktif semboller

    async def start_signal_broadcasting(self):
        """Start broadcasting trading signals"""
        while True:
            try:
                for symbol in self.active_symbols:
                    # Test sinyali oluştur
                    signal = {
                        "signal": "BUY",
                        "price": 50000,
                        "rsi": 25,
                        "timestamp": datetime.now().isoformat(),
                    }
                    await self.broadcast_signal(symbol, signal)

                await asyncio.sleep(10)  # 10 saniye bekle

            except Exception as e:
                logger.error(f"Error broadcasting signals: {e}")
                await asyncio.sleep(5)

    async def broadcast_signal(self, symbol: str, signal: Dict):
        """Broadcast signal to subscribed clients"""
        message = {
            "type": "signal",
            "symbol": symbol,
            "data": {
                "signal": signal.get("signal"),
                "price": signal.get("price"),
                "rsi": signal.get("rsi"),
                "timestamp": signal.get("timestamp"),
            },
        }
        await self.ws_manager.broadcast_update(symbol, message)
