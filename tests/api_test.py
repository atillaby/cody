import asyncio
import logging
from datetime import datetime

import aiohttp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://0.0.0.0:8000"


async def test_endpoint(session, method: str, endpoint: str, data: dict = None):
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            async with session.get(url) as response:
                result = await response.json()
        else:  # POST
            async with session.post(url, json=data) as response:
                result = await response.json()

        logger.info(f"{method} {endpoint} - Status: {response.status}")
        logger.info(f"Response: {result}")
        return response.status, result
    except Exception as e:
        logger.error(f"Error testing {endpoint}: {e}")
        return None, None


async def run_tests():
    async with aiohttp.ClientSession() as session:
        tests = [
            # Health check
            ("GET", "/health"),
            # Strategy endpoints
            ("GET", "/strategies/active"),
            ("GET", "/strategies/markets"),
            ("GET", "/strategies/performance/rsi_strategy"),
            # Trading endpoints
            (
                "POST",
                "/trading/market-order",
                {"symbol": "BTC-USDT", "side": "BUY", "amount": 0.001},
            ),
        ]

        for test in tests:
            method, endpoint, *data = test
            logger.info(f"\nTesting {method} {endpoint}")
            status, result = await test_endpoint(
                session, method, endpoint, data[0] if data else None
            )
            await asyncio.sleep(1)  # Rate limiting


if __name__ == "__main__":
    asyncio.run(run_tests())
