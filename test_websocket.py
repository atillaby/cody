import asyncio
import json
import logging

import websockets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_websocket():
    uri = "ws://0.0.0.0:8000/ws/test-client"
    async with websockets.connect(uri) as websocket:
        logger.info("Connected to WebSocket")

        # Test message gönder
        test_message = {"type": "subscribe", "symbol": "BTC-USDT"}
        await websocket.send(json.dumps(test_message))
        logger.info(f"Sent: {test_message}")

        # Yanıtı bekle
        response = await websocket.recv()
        logger.info(f"Received: {response}")


if __name__ == "__main__":
    asyncio.run(test_websocket())
