import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Tuple

import pandas as pd
from strategies.strategy_base import StrategyBase

from api.services.okx_service import OKXService
from api.services.telegram_service import TelegramService

logger = logging.getLogger(__name__)


class Strategy(StrategyBase):
    def calculate_bollinger_bands(
        self, close: List[float], period: int = 20, std_dev: float = 2
    ) -> Tuple[float, float, float]:
        try:
            close_series = pd.Series(close)
            sma = close_series.rolling(window=period).mean()
            std = close_series.rolling(window=period).std()
            upper_band = sma + (std * std_dev)
            lower_band = sma - (std * std_dev)

            return sma.iloc[-1], upper_band.iloc[-1], lower_band.iloc[-1]
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {str(e)}")
            return float("nan"), float("nan"), float("nan")

    async def check_signals(self, symbol: str):
        try:
            formatted_symbol = symbol.replace("-", "/")
            logger.info(f"Checking signals for {formatted_symbol}")
            ticker = self.okx.get_tickers()

            if isinstance(ticker, dict) and "error" in ticker:
                raise ValueError(f"Error fetching ticker: {ticker['error']}")

            if formatted_symbol not in ticker:
                available_symbols = list(ticker.keys())[:5]
                logger.error(
                    f"Symbol {formatted_symbol} not found. Available symbols: {available_symbols}"
                )
                raise ValueError(
                    f"Symbol {formatted_symbol} not found in available markets"
                )

            try:
                # OHLCV verilerini al
                ohlcv = await asyncio.to_thread(
                    self.okx.exchange.fetch_ohlcv,
                    formatted_symbol,
                    timeframe="1h",
                    limit=100,
                )

                if not ohlcv or len(ohlcv) < 20:  # Bollinger Bands için minimum veri
                    raise ValueError(f"Insufficient data for {formatted_symbol}")

                close = [float(candle[4]) for candle in ohlcv]  # Closing prices
                current_price = float(ticker[formatted_symbol]["last"])

                # Bollinger Bands hesapla
                sma, upper_band, lower_band = self.calculate_bollinger_bands(close)

                if pd.isna(sma) or pd.isna(upper_band) or pd.isna(lower_band):
                    raise ValueError(
                        f"Invalid Bollinger Bands value for {formatted_symbol}"
                    )

                logger.info(
                    f"{formatted_symbol} - Price: {current_price}, SMA: {sma}, Upper Band: {upper_band}, Lower Band: {lower_band}"
                )

                # Sinyal kontrolü
                signal = "NEUTRAL"
                if current_price > upper_band:
                    signal = "SELL"
                elif current_price < lower_band:
                    signal = "BUY"

                response = {
                    "symbol": formatted_symbol,
                    "signal": signal,
                    "price": current_price,
                    "sma": float(sma),
                    "upper_band": float(upper_band),
                    "lower_band": float(lower_band),
                    "timestamp": str(datetime.now()),
                }

                if signal != "NEUTRAL":
                    # İşlem limitlerini al
                    trading_limits = self.get_trading_limits(formatted_symbol)
                    logger.info(
                        f"Trading limits for {formatted_symbol}: {trading_limits}"
                    )

                    # Execute the trade
                    await self.execute_signal(
                        symbol=formatted_symbol,
                        signal=signal,
                        price=current_price,
                        indicator_value=sma,  # rsi yerine indicator_value kullan
                    )

                return response

            except Exception as e:
                logger.error(f"Error processing OHLCV data: {str(e)}")
                raise ValueError(f"Error processing market data: {str(e)}")

        except Exception as e:
            logger.error(f"Error checking signals: {str(e)}")
            return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    okx_service = OKXService()
    telegram_service = TelegramService()
    strategy = Strategy(okx_service, telegram_service)

    async def main():
        while True:
            await strategy.check_signals("BTC/USDT")
            await asyncio.sleep(60)  # 1 dakika bekleyin

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
