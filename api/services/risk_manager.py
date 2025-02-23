import logging
from decimal import Decimal
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self):
        self.max_position_size = 0.05  # Portföyün maksimum %5'i
        self.max_open_positions = 5
        self.stop_loss_percent = 0.01  # %1 stop-loss
        self.risk_reward_ratio = 2  # 1:2 risk/ödül oranı
        self.usdt_reserve = 0.20  # %20 USDT rezervi

    async def validate_trade(self, symbol: str, side: str, amount: Decimal,
                           portfolio_value: Decimal) -> Tuple[bool, str]:
        """İşlem validasyonu"""
        try:
            # Position büyüklüğü kontrolü
            position_size = amount / portfolio_value
            if position_size > self.max_position_size:
                return False, f"Position size {position_size:.2%} exceeds maximum {self.max_position_size:.2%}"

            # Açık pozisyon sayısı kontrolü
            if await self._get_open_positions_count() >= self.max_open_positions:
                return False, f"Maximum open positions ({self.max_open_positions}) reached"

            # USDT rezerv kontrolü
            if not await self._check_usdt_reserve(portfolio_value):
                return False, "Insufficient USDT reserve"

            return True, "Trade validated"
        except Exception as e:
            logger.error(f"Trade validation error: {e}")
            return False, str(e)

    async def calculate_position_size(self, symbol: str, portfolio_value: Decimal,
                                   risk_per_trade: Decimal) -> Decimal:
        """Pozisyon büyüklüğü hesapla"""
        try:
            max_position = portfolio_value * Decimal(str(self.max_position_size))
            risk_based_size = portfolio_value * risk_per_trade

            return min(max_position, risk_based_size)
        except Exception as e:
            logger.error(f"Position size calculation error: {e}")
            raise

    async def calculate_stop_levels(self, symbol: str, entry_price: Decimal,
                                  side: str) -> Dict[str, Decimal]:
        """Stop-loss ve take-profit seviyelerini hesapla"""
        try:
            stop_amount = entry_price * Decimal(str(self.stop_loss_percent))

            if side == "buy":
                stop_loss = entry_price - stop_amount
                take_profit = entry_price + (stop_amount * Decimal(str(self.risk_reward_ratio)))
            else:
                stop_loss = entry_price + stop_amount
                take_profit = entry_price - (stop_amount * Decimal(str(self.risk_reward_ratio)))

            return {
                "stop_loss": stop_loss,
                "take_profit": take_profit
            }
        except Exception as e:
            logger.error(f"Stop levels calculation error: {e}")
            raise
