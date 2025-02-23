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
    def calculate_keltner_channel(
        self,
        high: List[float],
        low: List[float],
        close: List[float],
        period: int = 20,
        atr_multiplier: float = 2,
    ) -> Tuple[float, float, float]:
        try:
            high_series = pd.Series(high)
            low_series = pd.Series(low)
            close_series = pd.Series(close)

            typical_price = (high_series + low_series + close_series) / 3
            sma = typical_price.rolling(window=period).mean()
            tr = pd.concat(
                [
                    high_series - low_series,
                    (high_series - close_series.shift()).abs(),
                    (low_series - close_series.shift()).abs(),
                ],
                axis=1,
            ).max(axis=1)
            atr = tr.rolling(window=period).mean()

            upper_band = sma + (atr * atr_multiplier)
            lower_band = sma - (atr * atr_multiplier)

            return sma.iloc[-1], upper_band.iloc[-1], lower_band.iloc[-1]
        except Exception as e:
            logger.error(f"Error calculating Keltner Channel: {str(e)}")
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

                if not ohlcv or len(ohlcv) < 20:  # Keltner Channel için minimum veri
                    raise ValueError(f"Insufficient data for {formatted_symbol}")

                high = [float(candle[2]) for candle in ohlcv]  # High prices
                low = [float(candle[3]) for candle in ohlcv]  # Low prices
                close = [float(candle[4]) for candle in ohlcv]  # Closing prices
                current_price = float(ticker[formatted_symbol]["last"])

                # Keltner Channel hesapla
                sma, upper_band, lower_band = self.calculate_keltner_channel(
                    high, low, close
                )

                if pd.isna(sma) or pd.isna(upper_band) or pd.isna(lower_band):
                    raise ValueError(
                        f"Invalid Keltner Channel value for {formatted_symbol}"
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
