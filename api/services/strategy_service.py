import asyncio
import logging
import os
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Type

import numpy as np
import pandas as pd

from api.services.okx_service import OKXService
from api.services.strategy_loader import load_strategies
from api.services.telegram_service import TelegramService

logger = logging.getLogger(__name__)


class StrategyService:
    def __init__(self, okx_service: OKXService, telegram_service: TelegramService):
        self.okx = okx_service
        self.telegram = telegram_service
        self.active_strategies = {}
        self.last_signals = {}
        self.strategies = self.load_all_strategies()

    def load_all_strategies(self) -> Dict[str, Type]:
        strategy_folder = os.path.join(os.path.dirname(__file__), "../../strategies")
        return load_strategies(strategy_folder)

    def format_symbol(self, symbol: str) -> str:
        """Convert BTC-USDT to BTC/USDT format"""
        return symbol.replace("-", "/")

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

    async def get_top_pairs(self, top_n: int = 20):
        """Get top trading pairs based on volume"""
        try:
            tickers = self.okx.get_tickers()
            if isinstance(tickers, dict) and "error" in tickers:
                raise ValueError(f"Error fetching tickers: {tickers['error']}")

            # Tickerları hacme göre sırala ve en iyi top_n çiftini seç
            sorted_tickers = sorted(
                tickers.items(), key=lambda x: x[1].get("quoteVolume", 0), reverse=True
            )
            top_pairs = sorted_tickers[:top_n]
            logger.info(f"Top {top_n} pairs: {top_pairs}")
            return [pair[0] for pair in top_pairs]

        except Exception as e:
            logger.error(f"Error fetching top pairs: {str(e)}")
            return []

    async def execute_signal(self, symbol: str, signal: str, price: float):
        """Execute trade based on signal"""
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
                    strategy_name="Auto-Trade", action=f"{signal} {symbol}", price=price
                )

            except Exception as e:
                logger.error(f"Order failed: {e}")
                await self.telegram.send_message(f"⚠️ Trade failed: {e}")

        except Exception as e:
            logger.error(f"Error executing signal: {e}")

    async def check_signals(self, symbol: str):
        try:
            formatted_symbol = self.format_symbol(symbol)
            logger.info(f"Checking signals for {formatted_symbol}")
            ticker = self.okx.get_tickers()  # await ifadesini kaldırdık

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
                        symbol=formatted_symbol, signal=signal, price=current_price
                    )

                return response

            except Exception as e:
                logger.error(f"Error processing OHLCV data: {str(e)}")
                raise ValueError(f"Error processing market data: {str(e)}")

        except Exception as e:
            logger.error(f"Error checking signals: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def get_markets(self):
        """Get all available markets"""
        try:
            tickers = await self.okx.get_tickers()
            return {
                "count": len(tickers),
                "markets": list(tickers.keys()),
            }
        except Exception as e:
            logger.error(f"Error fetching markets: {e}")
            raise

    async def run_strategy(self, strategy_id: str):
        try:
            logger.info(f"Starting strategy: {strategy_id}")

            # Strateji durumunu güncelle
            self.active_strategies[strategy_id].update(
                {
                    "status": "running",
                    "started_at": datetime.now().isoformat(),
                    "last_update": datetime.now().isoformat(),
                }
            )

            if strategy_id in self.strategies:
                strategy_class = self.strategies[strategy_id]
                strategy_instance = strategy_class(self.okx, self.telegram)
                symbols = await self.get_top_pairs()
                while True:
                    for symbol in symbols:
                        try:
                            result = await strategy_instance.check_signals(symbol)
                            self.last_signals[symbol] = result
                            self.active_strategies[strategy_id][
                                "last_update"
                            ] = datetime.now().isoformat()
                            self.active_strategies[strategy_id]["signals"].append(
                                result
                            )

                            # En son 10 sinyali tut
                            if len(self.active_strategies[strategy_id]["signals"]) > 10:
                                self.active_strategies[strategy_id][
                                    "signals"
                                ] = self.active_strategies[strategy_id]["signals"][-10:]

                            logger.info(f"Signal update for {symbol}: {result}")
                            await asyncio.sleep(5)
                        except Exception as e:
                            logger.error(f"Error checking {symbol}: {e}")

                    await asyncio.sleep(60)
            else:
                raise ValueError(f"Unknown strategy: {strategy_id}")

        except Exception as e:
            logger.error(f"Strategy failed: {e}")
            self.active_strategies[strategy_id].update(
                {
                    "status": "failed",
                    "error": str(e),
                    "failed_at": datetime.now().isoformat(),
                }
            )
            await self.telegram.send_message(f"⚠️ Strategy {strategy_id} failed: {e}")
            raise

    async def get_strategy_status(self, strategy_id: str):
        """Get current status of a strategy"""
        if strategy_id not in self.active_strategies:
            return {
                "status": "not_found",
                "message": f"Strategy {strategy_id} not found",
            }

        return self.active_strategies[strategy_id]

    async def get_last_signals(self):
        """Get last signals for all symbols"""
        if not self.last_signals:
            return {
                "status": "no_signals",
                "message": "No signals available yet",
                "signals": {},
            }
        return {"status": "success", "signals": self.last_signals}
