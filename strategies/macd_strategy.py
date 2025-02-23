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
    def calculate_macd(
        self,
        close: List[float],
        short_period: int = 12,
        long_period: int = 26,
        signal_period: int = 9,
    ):
        try:
            close_series = pd.Series(close)
            short_ema = close_series.ewm(span=short_period, adjust=False).mean()
            long_ema = close_series.ewm(span=long_period, adjust=False).mean()
            macd = short_ema - long_ema
            signal = macd.ewm(span=signal_period, adjust=False).mean()
            histogram = macd - signal

            return macd.iloc[-1], signal.iloc[-1], histogram.iloc[-1]
        except Exception as e:
            logger.error(f"Error calculating MACD: {str(e)}")
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

                if not ohlcv or len(ohlcv) < 26:  # MACD için minimum veri
                    raise ValueError(f"Insufficient data for {formatted_symbol}")

                close = [float(candle[4]) for candle in ohlcv]  # Closing prices
                current_price = float(ticker[formatted_symbol]["last"])

                # MACD hesapla
                macd, signal, histogram = self.calculate_macd(close)

                if pd.isna(macd) or pd.isna(signal) or pd.isna(histogram):
                    raise ValueError(f"Invalid MACD value for {formatted_symbol}")

                logger.info(
                    f"{formatted_symbol} - Price: {current_price}, MACD: {macd}, Signal: {signal}, Histogram: {histogram}"
                )

                # Sinyal kontrolü
                signal_type = "NEUTRAL"
                if macd > signal:
                    signal_type = "BUY"
                elif macd < signal:
                    signal_type = "SELL"

                response = {
                    "symbol": formatted_symbol,
                    "signal": signal_type,
                    "price": current_price,
                    "macd": float(macd),
                    "signal_line": float(signal),
                    "histogram": float(histogram),
                    "timestamp": str(datetime.now()),
                }

                if signal_type != "NEUTRAL":
                    # Execute the trade
                    await self.execute_signal(
                        symbol=formatted_symbol,
                        signal=signal_type,
                        price=current_price,
                        indicator_value=macd,  # rsi yerine indicator_value kullan
                    )

                return response

            except Exception as e:
                logger.error(f"Error processing OHLCV data: {str(e)}")
                raise ValueError(f"Error processing market data: {str(e)}")

        except Exception as e:
            logger.error(f"Error checking signals: {str(e)}")
            return {"status": "error", "message": str(e)}
