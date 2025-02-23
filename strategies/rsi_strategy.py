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
    def __init__(self, okx_service: OKXService, telegram_service: TelegramService):
        self.okx = okx_service
        self.telegram = telegram_service

    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        try:
            returns = pd.Series(prices).diff()
            gains = returns.where(returns > 0, 0)
            losses = -returns.where(returns < 0, 0)

            avg_gain = gains.rolling(window=period).mean()
            avg_loss = losses.rolling(window=period).mean()

            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1]
        except Exception as e:
            logger.error(f"Error calculating RSI: {str(e)}")
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

                if not ohlcv or len(ohlcv) < 14:  # RSI için minimum veri
                    raise ValueError(f"Insufficient data for {formatted_symbol}")

                prices = [float(candle[4]) for candle in ohlcv]  # Closing prices
                current_price = float(ticker[formatted_symbol]["last"])

                # RSI hesapla
                rsi = self.calculate_rsi(prices)

                if not isinstance(rsi, (int, float)) or pd.isna(rsi):
                    raise ValueError(f"Invalid RSI value for {formatted_symbol}")

                logger.info(f"{formatted_symbol} - Price: {current_price}, RSI: {rsi}")

                # Sinyal kontrolü
                signal = "NEUTRAL"
                if rsi < 30:
                    signal = "BUY"
                elif rsi > 70:
                    signal = "SELL"

                response = {
                    "symbol": formatted_symbol,
                    "signal": signal,
                    "price": current_price,
                    "rsi": float(rsi),
                    "timestamp": str(datetime.now()),
                }

                if signal != "NEUTRAL":
                    # Execute the trade
                    await self.execute_signal(
                        symbol=formatted_symbol,
                        signal=signal,
                        price=current_price,
                        rsi=rsi,
                    )

                return response

            except Exception as e:
                logger.error(f"Error processing OHLCV data: {str(e)}")
                raise ValueError(f"Error processing market data: {str(e)}")

        except Exception as e:
            logger.error(f"Error checking signals: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def execute_rsi_signal(
        self, symbol: str, signal: str, price: float, rsi: float
    ):
        """Execute trade based on RSI signal"""
        try:
            if signal == "NEUTRAL":
                return

            # Pozisyon büyüklüğünü hesapla (bakiyenin %1'i)
            balance = self.okx.get_balance()
            if balance.get("status") == "error":
                raise ValueError(f"Failed to fetch balance: {balance.get('message')}")

            usdt_balance = Decimal(str(balance.get("free", {}).get("USDT", 0)))
            position_size = (usdt_balance * Decimal("0.01")) / Decimal(str(price))

            # Minimum işlem tutarı kontrolü
            if position_size < Decimal("0.0001"):  # BTC minimum işlem tutarı
                logger.warning(f"Position size too small: {position_size} BTC")
                return

            # Yeterli bakiye kontrolü
            if usdt_balance < position_size * Decimal(str(price)):
                logger.warning(f"Insufficient USDT balance: {usdt_balance} USDT")
                await self.telegram.send_message(
                    f"⚠️ Insufficient USDT balance: {usdt_balance} USDT"
                )
                return

            # ETH bakiyesi kontrolü
            eth_balance = Decimal(str(balance.get("free", {}).get("ETH", 0)))
            if symbol.startswith("ETH") and eth_balance < position_size:
                logger.warning(f"Insufficient ETH balance: {eth_balance} ETH")
                await self.telegram.send_message(
                    f"⚠️ Insufficient ETH balance: {eth_balance} ETH"
                )
                return

            # Trade'i gerçekleştir
            try:
                side = "buy" if signal == "BUY" else "sell"
                order = self.okx.place_market_order(
                    symbol=symbol, side=side, amount=position_size
                )

                if order.get("status") == "error":
                    raise ValueError(f"Order failed: {order.get('message')}")

                logger.info(f"Order executed: {order}")
                await self.telegram.send_alert(
                    strategy_name="RSI Auto-Trade",
                    action=f"{signal} {symbol}",
                    price=price,
                )

            except Exception as e:
                logger.error(f"Order failed: {e}")
                await self.telegram.send_message(f"⚠️ Trade failed: {e}")

        except Exception as e:
            logger.error(f"Error executing RSI signal: {e}")
