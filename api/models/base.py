from typing import Dict, List, Optional

from pydantic import BaseModel


class StrategyBase(BaseModel):
    id: str
    name: str
    symbol: str
    timeframe: str
    status: str = "inactive"


class TradeBase(BaseModel):
    symbol: str
    side: str
    amount: float
    price: Optional[float] = None
