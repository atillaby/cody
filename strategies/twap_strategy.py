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
    def calculate_twap(self, close: List[float], period: int = 14) -> float:
        try:
            close_series = pd.Series(close)
            twap = close_series.rolling(window=period).mean()
            return twap.iloc[-1]
        except Exception as e:
            logger.error(f"Error calculating TWAP: {str(e)}")
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

                if not ohlcv or len(ohlcv) < 14:  # TWAP için minimum veri
                    raise ValueError(f"Insufficient data for {formatted_symbol}")

                close = [float(candle[4]) for candle in ohlcv]  # Closing prices
                current_price = float(ticker[formatted_symbol]["last"])

                # TWAP hesapla
                twap = self.calculate_twap(close)

                if not isinstance(twap, (int, float)) or pd.isna(twap):
                    raise ValueError(f"Invalid TWAP value for {formatted_symbol}")

                logger.info(
                    f"{formatted_symbol} - Price: {current_price}, TWAP: {twap}"
                )

                # Sinyal kontrolü
                signal = "NEUTRAL"
                if current_price > twap:
                    signal = "BUY"
                elif current_price < twap:
                    signal = "SELL"

                response = {
                    "symbol": formatted_symbol,
                    "signal": signal,
                    "price": current_price,
                    "twap": float(twap),
                    "timestamp": str(datetime.now()),
                }

                if signal != "NEUTRAL":
                    # Execute the trade
                    await self.execute_signal(
                        symbol=formatted_symbol,
                        signal=signal,
                        price=current_price,
                        indicator_value=twap,  # rsi yerine indicator_value kullan
                    )

                return response

            except Exception as e:
                logger.error(f"Error processing OHLCV data: {str(e)}")
                raise ValueError(f"Error processing market data: {str(e)}")

        except Exception as e:
            logger.error(f"Error checking signals: {str(e)}")
            return {"status": "error", "message": str(e)}
