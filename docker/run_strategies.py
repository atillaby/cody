import asyncio
import logging

from strategies.adx_strategy import Strategy as ADXStrategy
from strategies.atr_strategy import Strategy as ATRStrategy
from strategies.bollinger_bands_strategy import Strategy as BollingerBandsStrategy
from strategies.cci_strategy import Strategy as CCIStrategy
from strategies.fibonacci_strategy import Strategy as FibonacciStrategy
from strategies.heiken_ashi_strategy import Strategy as HeikenAshiStrategy
from strategies.keltner_channel_strategy import Strategy as KeltnerChannelStrategy
from strategies.macd_strategy import Strategy as MACDStrategy
from strategies.rsi_strategy import Strategy as RSIStrategy
from strategies.twap_strategy import Strategy as TWAPStrategy
from strategies.vwap_strategy import Strategy as VWAPStrategy

from api.services.okx_service import OKXService
from api.services.telegram_service import TelegramService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_strategies():
    # Servisleri başlat
    okx_service = OKXService()
    telegram_service = TelegramService()

    # Strateji listesini oluştur
    strategies = [
        ADXStrategy(okx_service, telegram_service),
        ATRStrategy(okx_service, telegram_service),
        BollingerBandsStrategy(okx_service, telegram_service),
        CCIStrategy(okx_service, telegram_service),
        FibonacciStrategy(okx_service, telegram_service),
        HeikenAshiStrategy(okx_service, telegram_service),
        KeltnerChannelStrategy(okx_service, telegram_service),
        MACDStrategy(okx_service, telegram_service),
        RSIStrategy(okx_service, telegram_service),
        TWAPStrategy(okx_service, telegram_service),
        VWAPStrategy(okx_service, telegram_service),
    ]

    while True:
        try:
            for strategy in strategies:
                strategy_name = strategy.__class__.__name__
                logger.info(f"Running {strategy_name}")
                try:
                    await strategy.check_signals("BTC/USDT")
                except Exception as e:
                    logger.error(f"Error in {strategy_name}: {e}")

            # Her strateji döngüsünden sonra 1 dakika bekle
            await asyncio.sleep(60)

        except Exception as e:
            logger.error(f"Main loop error: {e}")
            await asyncio.sleep(60)  # Hata durumunda da bekle


if __name__ == "__main__":
    logger.info("Starting strategy manager...")
    asyncio.run(run_strategies())
