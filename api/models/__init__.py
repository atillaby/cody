from typing import List, Optional

from pydantic import BaseModel


class Strategy(BaseModel):
    id: str
    name: str
    type: str
    timeframe: str
    risk_parameters: dict
