import asyncio
import json
import logging

from websockets import connect

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_connection():
    """Test WebSocket connection"""
    uri = "ws://0.0.0.0:8000/ws/test-client"

    try:
        async with connect(uri) as ws:
            logger.info("Connected to WebSocket server")

            # Subscribe to BTC/USDT
            await ws.send(json.dumps({"action": "subscribe", "symbol": "BTC/USDT"}))

            # Listen for messages
            while True:
                try:
                    msg = await ws.recv()
                    logger.info(f"Received: {msg}")
                except Exception as e:
                    logger.error(f"Error receiving message: {e}")
                    break

    except Exception as e:
        logger.error(f"Connection failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_connection())
