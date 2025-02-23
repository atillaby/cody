import asyncio
import json
import logging
import sys

import websockets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    uri = "ws://localhost:8000/ws/test1"
    retry_delay = 5
    max_retries = 3

    for attempt in range(max_retries):
        try:
            logger.info(f"Connecting to {uri} (Attempt {attempt + 1}/{max_retries})")
            async with websockets.connect(uri) as ws:
                logger.info("Connected!")

                msg = {"action": "subscribe", "symbol": "BTC/USDT"}

                await ws.send(json.dumps(msg))
                logger.info(f"Sent: {msg}")

                while True:
                    response = await ws.recv()
                    logger.info(f"Received: {response}")

        except ConnectionRefusedError:
            logger.error(f"Connection refused. Retrying in {retry_delay} seconds...")
            await asyncio.sleep(retry_delay)
        except Exception as e:
            logger.error(f"Error: {e}")
            if attempt == max_retries - 1:
                sys.exit(1)
            await asyncio.sleep(retry_delay)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
