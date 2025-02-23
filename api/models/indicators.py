from typing import List, Optional

from pydantic import BaseModel


class RSIConfig(BaseModel):
    period: int = 14
    overbought: float = 70.0
    oversold: float = 30.0


class IndicatorConfig(BaseModel):
    rsi: Optional[RSIConfig]
    use_macd: bool = False
    use_bollinger: bool = False
