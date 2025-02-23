from typing import List, Optional

from pydantic import BaseModel


class StatusResponse(BaseModel):
    trading: bool
    active_pairs: int
    total_strategies: int
    current_balance: str


class StrategyResponse(BaseModel):
    id: str
    name: str
    active: bool
    performance: float


class WebSocketMessage(BaseModel):
    type: str
    data: dict
