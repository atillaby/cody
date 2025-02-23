import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List

import pandas as pd
from strategies.strategy_base import StrategyBase

from api.services.okx_service import OKXService
from api.services.telegram_service import TelegramService

logger = logging.getLogger(__name__)


class Strategy(StrategyBase):
    def calculate_fibonacci_levels(self, high: float, low: float) -> Dict[str, float]:
        levels = {
            "level_0": low,
            "level_236": low + 0.236 * (high - low),
            "level_382": low + 0.382 * (high - low),
            "level_50": low + 0.5 * (high - low),
            "level_618": low + 0.618 * (high - low),
            "level_786": low + 0.786 * (high - low),
            "level_100": high,
        }
        return levels

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

                if not ohlcv or len(ohlcv) < 14:  # Fibonacci için minimum veri
                    raise ValueError(f"Insufficient data for {formatted_symbol}")

                high = max([float(candle[2]) for candle in ohlcv])  # High prices
                low = min([float(candle[3]) for candle in ohlcv])  # Low prices
                current_price = float(ticker[formatted_symbol]["last"])

                # Fibonacci seviyelerini hesapla
                fib_levels = self.calculate_fibonacci_levels(high, low)

                logger.info(
                    f"{formatted_symbol} - Price: {current_price}, Fibonacci Levels: {fib_levels}"
                )

                # Sinyal kontrolü
                signal = "NEUTRAL"
                if current_price <= fib_levels["level_236"]:
                    signal = "BUY"
                elif current_price >= fib_levels["level_786"]:
                    signal = "SELL"

                response = {
                    "symbol": formatted_symbol,
                    "signal": signal,
                    "price": current_price,
                    "fibonacci_levels": fib_levels,
                    "timestamp": str(datetime.now()),
                }

                if signal != "NEUTRAL":
                    # Execute the trade
                    await self.execute_signal(
                        symbol=formatted_symbol,
                        signal=signal,
                        price=current_price,
                        rsi=0,  # Fibonacci stratejisinde RSI kullanılmıyor
                    )

                return response

            except Exception as e:
                logger.error(f"Error processing OHLCV data: {str(e)}")
                raise ValueError(f"Error processing market data: {str(e)}")

        except Exception as e:
            logger.error(f"Error checking signals: {str(e)}")
            return {"status": "error", "message": str(e)}
