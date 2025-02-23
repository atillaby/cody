import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from typing import List

import pandas as pd
from strategies.strategy_base import StrategyBase

from api.services.okx_service import OKXService
from api.services.telegram_service import TelegramService

logger = logging.getLogger(__name__)


class Strategy(StrategyBase):
    def calculate_heiken_ashi(
        self,
        open_prices: List[float],
        high: List[float],
        low: List[float],
        close: List[float],
    ):
        try:
            df = pd.DataFrame(
                {"open": open_prices, "high": high, "low": low, "close": close}
            )

            heiken_ashi = pd.DataFrame(
                index=df.index, columns=["open", "high", "low", "close"]
            )
            heiken_ashi["close"] = (
                df["open"] + df["high"] + df["low"] + df["close"]
            ) / 4

            for i in range(len(df)):
                if i == 0:
                    heiken_ashi.iat[i, 0] = df["open"].iat[i]
                else:
                    heiken_ashi.iat[i, 0] = (
                        heiken_ashi.iat[i - 1, 0] + heiken_ashi.iat[i - 1, 3]
                    ) / 2

            heiken_ashi["high"] = df[["high", "open", "close"]].max(axis=1)
            heiken_ashi["low"] = df[["low", "open", "close"]].min(axis=1)

            return heiken_ashi
        except Exception as e:
            logger.error(f"Error calculating Heiken Ashi: {str(e)}")
            return None

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

                if not ohlcv or len(ohlcv) < 14:  # Heiken Ashi için minimum veri
                    raise ValueError(f"Insufficient data for {formatted_symbol}")

                open_prices = [float(candle[1]) for candle in ohlcv]  # Open prices
                high = [float(candle[2]) for candle in ohlcv]  # High prices
                low = [float(candle[3]) for candle in ohlcv]  # Low prices
                close = [float(candle[4]) for candle in ohlcv]  # Closing prices
                current_price = float(ticker[formatted_symbol]["last"])

                # Heiken Ashi hesapla
                heiken_ashi = self.calculate_heiken_ashi(open_prices, high, low, close)

                if heiken_ashi is None or heiken_ashi.empty:
                    raise ValueError(
                        f"Invalid Heiken Ashi value for {formatted_symbol}"
                    )

                ha_close = heiken_ashi["close"].iloc[-1]
                ha_open = heiken_ashi["open"].iloc[-1]

                logger.info(
                    f"{formatted_symbol} - Price: {current_price}, Heiken Ashi Close: {ha_close}, Heiken Ashi Open: {ha_open}"
                )

                # Sinyal kontrolü
                signal = "NEUTRAL"
                if ha_close > ha_open:
                    signal = "BUY"
                elif ha_close < ha_open:
                    signal = "SELL"

                response = {
                    "symbol": formatted_symbol,
                    "signal": signal,
                    "price": current_price,
                    "heiken_ashi_close": float(ha_close),
                    "heiken_ashi_open": float(ha_open),
                    "timestamp": str(datetime.now()),
                }

                if signal != "NEUTRAL":
                    await self.execute_signal(
                        symbol=formatted_symbol,
                        signal=signal,
                        price=current_price,
                        indicator_value=ha_close,  # rsi yerine indicator_value kullan
                    )

                return response

            except Exception as e:
                logger.error(f"Error processing OHLCV data: {str(e)}")
                raise ValueError(f"Error processing market data: {str(e)}")

        except Exception as e:
            logger.error(f"Error checking signals: {str(e)}")
            return {"status": "error", "message": str(e)}
