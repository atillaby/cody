import logging
from decimal import Decimal
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException

from api.models.base import TradeBase
from api.services.okx_service import OKXService
from api.services.telegram_service import TelegramService
from api.services.trade_service import TradeService

router = APIRouter(prefix="/trading", tags=["Trading"])
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/trading", tags=["Trading"])


def get_trade_service(
    okx_service: OKXService = Depends(), telegram_service: TelegramService = Depends()
):
    return TradeService(okx_service, telegram_service)


@router.get("/")
async def get_trading_status():
    return {"status": "active"}


@router.post("/market-order")
async def place_market_order(
    trade: TradeBase, trade_service: TradeService = Depends(get_trade_service)
):
    """Place a market order"""
    try:
        if not trade.amount or trade.amount <= 0:
            raise HTTPException(
                status_code=400, detail="Invalid amount: must be greater than 0"
            )

        order = await trade_service.execute_market_order(
            symbol=trade.symbol,
            side=trade.side.upper(),
            amount=Decimal(str(trade.amount)),
        )
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
