import asyncio
import logging

import websockets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test():
    uri = "ws://127.0.0.1:8000/ws/test-client"

    try:
        async with websockets.connect(uri) as ws:
            logger.info("Connected to WebSocket server")

            # Send a test message
            test_msg = "Hello, WebSocket!"
            await ws.send(test_msg)
            logger.info(f"Sent: {test_msg}")

            # Wait for response
            response = await ws.recv()
            logger.info(f"Received: {response}")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")


if __name__ == "__main__":
    asyncio.run(test())
