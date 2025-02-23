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
    def calculate_vwap(
        self,
        high: List[float],
        low: List[float],
        close: List[float],
        volume: List[float],
    ) -> float:
        try:
            high_series = pd.Series(high)
            low_series = pd.Series(low)
            close_series = pd.Series(close)
            volume_series = pd.Series(volume)

            typical_price = (high_series + low_series + close_series) / 3
            vwap = (typical_price * volume_series).cumsum() / volume_series.cumsum()

            return vwap.iloc[-1]
        except Exception as e:
            logger.error(f"Error calculating VWAP: {str(e)}")
            return float("nan")

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

                if not ohlcv or len(ohlcv) < 14:  # VWAP için minimum veri
                    raise ValueError(f"Insufficient data for {formatted_symbol}")

                high = [float(candle[2]) for candle in ohlcv]  # High prices
                low = [float(candle[3]) for candle in ohlcv]  # Low prices
                close = [float(candle[4]) for candle in ohlcv]  # Closing prices
                volume = [float(candle[5]) for candle in ohlcv]  # Volume
                current_price = float(ticker[formatted_symbol]["last"])

                # VWAP hesapla
                vwap = self.calculate_vwap(high, low, close, volume)

                if not isinstance(vwap, (int, float)) or pd.isna(vwap):
                    raise ValueError(f"Invalid VWAP value for {formatted_symbol}")

                logger.info(
                    f"{formatted_symbol} - Price: {current_price}, VWAP: {vwap}"
                )

                # Sinyal kontrolü
                signal = "NEUTRAL"
                if current_price > vwap:
                    signal = "BUY"
                elif current_price < vwap:
                    signal = "SELL"

                response = {
                    "symbol": formatted_symbol,
                    "signal": signal,
                    "price": current_price,
                    "vwap": float(vwap),
                    "timestamp": str(datetime.now()),
                }

                if signal != "NEUTRAL":
                    # Execute the trade
                    await self.execute_signal(
                        symbol=formatted_symbol,
                        signal=signal,
                        price=current_price,
                        indicator_value=vwap,  # rsi yerine indicator_value kullan
                    )

                return response

            except Exception as e:
                logger.error(f"Error processing OHLCV data: {str(e)}")
                raise ValueError(f"Error processing market data: {str(e)}")

        except Exception as e:
            logger.error(f"Error checking signals: {str(e)}")
            return {"status": "error", "message": str(e)}
