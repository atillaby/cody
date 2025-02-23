import asyncio
import json
import logging

import websockets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_websocket():
    uri = "ws://localhost:8000/ws/test-client"
    async with websockets.connect(uri) as websocket:
        # Subscribe to BTC/USDT updates
        subscribe_msg = {"action": "subscribe", "symbol": "BTC/USDT"}
        await websocket.send(json.dumps(subscribe_msg))
        logger.info(f"Sent subscription request: {subscribe_msg}")

        # Listen for updates
        while True:
            try:
                response = await websocket.recv()
                logger.info(f"Received: {response}")
            except Exception as e:
                logger.error(f"Error: {e}")
                break


if __name__ == "__main__":
    asyncio.run(test_websocket())
