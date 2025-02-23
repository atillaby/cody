from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class Trade(BaseModel):
    symbol: str
    side: str  # BUY or SELL
    quantity: Decimal
    price: Decimal
    type: str = "MARKET"  # MARKET, LIMIT
    status: str = "NEW"
    timestamp: datetime = datetime.utcnow()
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
