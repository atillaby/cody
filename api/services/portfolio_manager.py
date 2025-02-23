import asyncio
import logging
from datetime import datetime

from api.services.okx_service import OKXService

logger = logging.getLogger(__name__)


class PortfolioManager:
    def __init__(self, okx_service: OKXService):
        self.okx = okx_service
        self.portfolio = {}
        self.initial_balance = None
        self.watched_pairs = set()

    async def initialize_portfolio(self):
        """Başlangıç portföy değerlerini al ve kaydet"""
        try:
            balances = self.okx.get_balances()
            if balances:
                self.initial_balance = balances
                self.portfolio = balances["total"]
                logger.info("=== Initial Portfolio Status ===")
                logger.info(f"Total Balance: {self.get_portfolio_value()} USDT")
                for currency, amount in self.portfolio.items():
                    if float(amount) > 0:
                        logger.info(f"{currency}: {amount}")
                logger.info("==============================")
                return True
            return False
        except Exception as e:
            logger.error(f"Error initializing portfolio: {e}")
            return False

    def update_portfolio(self):
        """Portföy değerlerini güncelle"""
        try:
            balances = self.okx.get_balances()
            if balances:
                old_portfolio = self.portfolio.copy()
                self.portfolio = balances["total"]

                # Değişiklikleri logla
                for currency in set(self.portfolio.keys()) | set(old_portfolio.keys()):
                    old_amount = old_portfolio.get(currency, 0)
                    new_amount = self.portfolio.get(currency, 0)
                    if old_amount != new_amount:
                        logger.info(
                            f"Portfolio Update - {currency}: {old_amount} -> {new_amount}"
                        )

                return True
            return False
        except Exception as e:
            logger.error(f"Error updating portfolio: {e}")
            return False

    async def monitor_pairs(self):
        """İzlenen çiftleri sürekli kontrol et"""
        while True:
            try:
                tickers = self.okx.get_tickers()
                for symbol in self.watched_pairs:
                    if symbol in tickers:
                        ticker = tickers[symbol]
                        logger.info(
                            f"[{datetime.now().strftime('%H:%M:%S')}] {symbol} - "
                            f"Price: {ticker['last']}, "
                            f"24h Volume: {ticker['quoteVolume']}, "
                            f"24h Change: {ticker['percentage']}%"
                        )
            except Exception as e:
                logger.error(f"Error monitoring pairs: {e}")
            await asyncio.sleep(10)  # 10 saniye bekle

    def add_watched_pair(self, symbol: str):
        """İzlenecek çift ekle"""
        self.watched_pairs.add(symbol)
        logger.info(f"Now watching: {symbol}")

    def remove_watched_pair(self, symbol: str):
        """İzlenen çifti çıkar"""
        self.watched_pairs.discard(symbol)
        logger.info(f"Stopped watching: {symbol}")

    def get_portfolio_value(self) -> float:
        """Toplam portföy değerini hesapla"""
        try:
            tickers = self.okx.get_tickers()
            total_value = 0
            for currency, amount in self.portfolio.items():
                if currency == "USDT":
                    total_value += float(amount)
                else:
                    symbol = f"{currency}/USDT"
                    if symbol in tickers:
                        price = float(tickers[symbol]["last"])
                        value = float(amount) * price
                        total_value += value
            return total_value
        except Exception as e:
            logger.error(f"Error calculating portfolio value: {e}")
            return 0
