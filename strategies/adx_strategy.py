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
    def calculate_adx(
        self, high: List[float], low: List[float], close: List[float], period: int = 14
    ) -> float:
        try:
            high_series = pd.Series(high)
            low_series = pd.Series(low)
            close_series = pd.Series(close)

            plus_dm = high_series.diff()
            minus_dm = low_series.diff()

            plus_dm[plus_dm < 0] = 0
            minus_dm[minus_dm > 0] = 0

            tr1 = high_series - low_series
            tr2 = (high_series - close_series.shift()).abs()
            tr3 = (low_series - close_series.shift()).abs()

            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(window=period).mean()

            plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
            minus_di = 100 * (minus_dm.abs().rolling(window=period).mean() / atr)

            dx = (plus_di - minus_di).abs() / (plus_di + minus_di) * 100
            adx = dx.rolling(window=period).mean()

            return adx.iloc[-1]
        except Exception as e:
            logger.error(f"Error calculating ADX: {str(e)}")
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

                if not ohlcv or len(ohlcv) < 14:  # ADX için minimum veri
                    raise ValueError(f"Insufficient data for {formatted_symbol}")

                high = [float(candle[2]) for candle in ohlcv]  # High prices
                low = [float(candle[3]) for candle in ohlcv]  # Low prices
                close = [float(candle[4]) for candle in ohlcv]  # Closing prices
                current_price = float(ticker[formatted_symbol]["last"])

                # ADX hesapla
                adx = self.calculate_adx(high, low, close)

                if not isinstance(adx, (int, float)) or pd.isna(adx):
                    raise ValueError(f"Invalid ADX value for {formatted_symbol}")

                logger.info(f"{formatted_symbol} - Price: {current_price}, ADX: {adx}")

                # Sinyal kontrolü
                signal = "NEUTRAL"
                if adx > 25:
                    if current_price > close[-1]:
                        signal = "BUY"
                    elif current_price < close[-1]:
                        signal = "SELL"

                response = {
                    "symbol": formatted_symbol,
                    "signal": signal,
                    "price": current_price,
                    "adx": float(adx),
                    "timestamp": str(datetime.now()),
                }

                if signal != "NEUTRAL":
                    await self.execute_signal(
                        symbol=formatted_symbol,
                        signal=signal,
                        price=current_price,
                        indicator_value=adx,  # rsi yerine indicator_value kullan
                    )

                return response

            except Exception as e:
                logger.error(f"Error processing OHLCV data: {str(e)}")
                raise ValueError(f"Error processing market data: {str(e)}")

        except Exception as e:
            logger.error(f"Error checking signals: {str(e)}")
            return {"status": "error", "message": str(e)}
