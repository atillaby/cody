import asyncio
import json  # JSON için ekledik
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import List

import pandas as pd

import redis
from api.services.okx_service import OKXService
from api.services.telegram_service import TelegramService

logger = logging.getLogger(__name__)


class StrategyBase(ABC):
    def __init__(self, okx_service: OKXService, telegram_service: TelegramService):
        self.okx = okx_service
        self.telegram = telegram_service
        self.redis_client = redis.Redis(host="redis", port=6379, db=0)

    @abstractmethod
    async def check_signals(self, symbol: str):
        pass

    async def save_signal(
        self,
        symbol: str,
        signal: str,
        price: float,
        indicator_value: float,
        strategy_name: str,
    ):
        """Sinyal bilgisini Redis'e kaydet"""
        try:
            signal_data = {
                "symbol": symbol,
                "signal": signal,
                "price": float(price),  # float'a çevir
                "indicator_value": float(indicator_value),  # float'a çevir
                "strategy": strategy_name,
                "timestamp": str(datetime.now()),
            }

            # Mevcut sinyalleri al
            signals_bytes = self.redis_client.get("strategy_signals")
            if signals_bytes:
                signals = json.loads(signals_bytes.decode("utf-8"))
            else:
                signals = []

            # Yeni sinyali ekle (en fazla son 100 sinyal tutulur)
            signals.insert(0, signal_data)
            signals = signals[:100]

            # Redis'e JSON olarak kaydet
            self.redis_client.set("strategy_signals", json.dumps(signals))

            logger.info(f"Signal saved: {signal_data}")
        except Exception as e:
            logger.error(f"Error saving signal: {e}")

    async def execute_signal(
        self, symbol: str, signal: str, price: float, indicator_value: float
    ):
        logger.info(
            f"Executing {signal} signal for {symbol} at price {price} with indicator value {indicator_value}"
        )
        try:
            # Sinyali kaydet
            await self.save_signal(
                symbol, signal, price, indicator_value, self.__class__.__name__
            )

            if signal == "BUY":
                # Alış işlemi
                logger.info(f"Buying {symbol} at price {price}")
                trading_limits = self.get_trading_limits(symbol)
                logger.info(f"Trading limits for {symbol}: {trading_limits}")
            elif signal == "SELL":
                # Satış işlemi
                logger.info(f"Selling {symbol} at price {price}")
            else:
                logger.warning(f"Unknown signal: {signal}")

        except Exception as e:
            logger.error(f"Error executing signal: {str(e)}")
            raise

    def get_trading_limits(self, symbol: str):
        try:
            trading_limits_bytes = self.redis_client.get("trading_limits")
            if trading_limits_bytes is None:
                logger.info("Trading limits not found in Redis, fetching from OKX...")
                trading_limits = self.okx.get_trading_limits()
                if trading_limits:
                    self.redis_client.set("trading_limits", json.dumps(trading_limits))
                    return trading_limits.get(symbol, {})
                return {}

            trading_limits = json.loads(trading_limits_bytes.decode("utf-8"))
            logger.info(f"Successfully fetched trading limits from Redis for {symbol}")
            return trading_limits.get(symbol, {})
        except Exception as e:
            logger.error(f"Error fetching trading limits: {str(e)}")
            return {}
