from typing import Optional

from pydantic import BaseModel


class StrategyRequest(BaseModel):
    name: str
    parameters: dict
    active: bool = True
