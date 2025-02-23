import asyncio
import logging
from decimal import Decimal

from api.services.okx_service import OKXService
from api.services.strategy_service import StrategyService
from api.services.telegram_service import TelegramService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_trading():
    try:
        # Servisleri başlat
        okx = OKXService()
        telegram = TelegramService()
        strategy = StrategyService(okx, telegram)

        # 1. Mevcut sembolleri kontrol et
        logger.info("Checking available symbols...")
        tickers = await okx.get_tickers()
        symbols = list(tickers.keys())
        logger.info(f"First 5 available symbols: {symbols[:5]}")

        # 2. BTC/USDT sinyallerini kontrol et
        test_symbol = "BTC/USDT"
        logger.info(f"Checking signals for {test_symbol}...")
        signals = await strategy.check_signals(test_symbol)
        logger.info(f"Signal results: {signals}")

        # 3. Hesap bakiyesini kontrol et
        logger.info("Checking account balance...")
        balance = await okx.get_balance()
        logger.info(f"Balance: {balance.get('total', {})}")

    except Exception as e:
        logger.error(f"Test failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_trading())
