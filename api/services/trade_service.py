import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation

from api.services.okx_service import OKXService
from api.services.telegram_service import TelegramService

logger = logging.getLogger(__name__)


class TradeService:
    def __init__(self, okx_service: OKXService, telegram_service: TelegramService):
        self.okx = okx_service
        self.telegram = telegram_service

    async def get_ticker_price(self, symbol: str) -> Decimal:
        """Get current market price for symbol"""
        try:
            tickers = await self.okx.get_tickers()
            if symbol not in tickers:
                raise ValueError(f"Symbol {symbol} not found")
            return Decimal(str(tickers[symbol]["last"]))
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            raise ValueError(f"Could not get price for {symbol}")

    async def check_balance(self, symbol: str, amount: Decimal, side: str) -> bool:
        """Check if there's sufficient balance for the trade"""
        try:
            balance = await self.okx.get_balance()

            if side.upper() == "BUY":
                quote_currency = symbol.split("-")[1]  # USDT from BTC-USDT
                current_price = await self.get_ticker_price(symbol)
                required_amount = amount * current_price * Decimal("1.01")  # %1 margin
                available = Decimal(str(balance.get("free", {}).get(quote_currency, 0)))

                logger.info(
                    f"Balance check for BUY - Required {quote_currency}: {required_amount}, Available: {available}"
                )
                return available >= required_amount
            else:  # SELL
                base_currency = symbol.split("-")[0]  # BTC from BTC-USDT
                available = Decimal(str(balance.get("free", {}).get(base_currency, 0)))

                logger.info(
                    f"Balance check for SELL - Required {base_currency}: {amount}, Available: {available}"
                )
                return available >= amount

        except Exception as e:
            logger.error(f"Balance check failed: {e}")
            return False

    async def execute_market_order(self, symbol: str, side: str, amount: Decimal):
        """Execute a market order with balance check"""
        try:
            # Input validation
            if not symbol or not side or not amount:
                raise ValueError("Missing required parameters")

            if amount <= 0:
                raise ValueError("Amount must be positive")

            # Check balance
            if not await self.check_balance(symbol, amount, side):
                current_balance = await self.okx.get_balance()
                raise ValueError(
                    f"Insufficient balance. Current balance: {current_balance.get('free', {})}"
                )

            logger.info(f"Executing {side} order for {amount} {symbol}")

            # Place order
            order = await self.okx.place_market_order(
                symbol=symbol, side=side.upper(), amount=amount
            )

            await self.telegram.send_alert(
                strategy_name="Live Trading",
                action=f"{side} {symbol}",
                price=float(order.get("price", 0)),
            )

            return order

        except ValueError as e:
            error_msg = f"Trade failed: {str(e)}"
            logger.error(error_msg)
            await self.telegram.send_message(f"⚠️ {error_msg}")
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            await self.telegram.send_message(f"❌ {error_msg}")
            raise ValueError(error_msg)
