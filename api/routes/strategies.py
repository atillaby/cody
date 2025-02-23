import logging
from typing import Dict, List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from api.services.okx_service import OKXService
from api.services.strategy_service import StrategyService
from api.services.telegram_service import TelegramService

logger = logging.getLogger(__name__)
router = APIRouter()


def get_okx_service():
    return OKXService()


def get_telegram_service():
    return TelegramService()


def get_strategy_service(
    okx_service: OKXService = Depends(get_okx_service),
    telegram_service: TelegramService = Depends(get_telegram_service),
):
    return StrategyService(okx_service, telegram_service)


@router.get("/")
async def get_strategies():
    """List all available strategies"""
    return {
        "strategies": [
            {
                "id": "rsi_strategy",
                "name": "RSI Strategy",
                "symbol": "BTC/USDT",
                "timeframe": "1h",
                "description": "RSI based trading strategy",
            }
        ]
    }


@router.get("/active")
async def get_active_strategies() -> List[str]:
    """Aktif stratejileri listele"""
    return [
        "ADX Strategy",
        "Bollinger Bands Strategy",
        "CCI Strategy",
        "Heiken Ashi Strategy",
        "Keltner Channel Strategy",
        "MACD Strategy",
        "RSI Strategy",
        "TWAP Strategy",
        "VWAP Strategy",
    ]


@router.get("/markets")
async def get_markets(
    strategy_service: StrategyService = Depends(get_strategy_service),
):
    """Get all available markets"""
    try:
        return await strategy_service.get_markets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start/{strategy_id}")
async def start_strategy(
    strategy_id: str,
    background_tasks: BackgroundTasks,
    strategy_service: StrategyService = Depends(get_strategy_service),
):
    """Start a trading strategy"""
    try:
        background_tasks.add_task(strategy_service.run_strategy, strategy_id)
        return {
            "status": "started",
            "strategy_id": strategy_id,
            "message": "Strategy started in background",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stop/{strategy_id}")
async def stop_strategy(strategy_id: str):
    """Stop a trading strategy"""
    return {"status": "stopped", "strategy_id": strategy_id}


@router.get("/performance/{strategy_id}")
async def get_strategy_performance(strategy_id: str):
    """Get performance metrics for a strategy"""
    return {
        "strategy_id": strategy_id,
        "win_rate": 65.5,
        "profit_loss": 12.3,
        "trades": 45,
    }


@router.get("/status/{strategy_id}")
async def get_strategy_status(
    strategy_id: str, strategy_service: StrategyService = Depends(get_strategy_service)
):
    """Get current status of a strategy"""
    try:
        status = await strategy_service.get_strategy_status(strategy_id)
        if status["status"] == "not_found":
            raise HTTPException(status_code=404, detail="Strategy not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals", response_model=Dict)
async def get_signals(
    strategy_service: StrategyService = Depends(get_strategy_service),
):
    """Get current trading signals"""
    try:
        signals = await strategy_service.get_last_signals()
        if not signals or signals.get("status") == "no_signals":
            return {"status": "success", "message": "No active signals", "signals": {}}
        return signals
    except Exception as e:
        logger.error(f"Error fetching signals: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch signals: {str(e)}"
        )


@router.get("/top_pairs")
async def get_top_pairs(
    strategy_service: StrategyService = Depends(get_strategy_service), top_n: int = 20
):
    """Get top trading pairs based on volume"""
    try:
        top_pairs = await strategy_service.get_top_pairs(top_n)
        logger.info(f"Fetched top pairs: {top_pairs}")
        return {"top_pairs": top_pairs}
    except Exception as e:
        logger.error(f"Error fetching top pairs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/balance")
async def get_balance(okx_service: OKXService = Depends(get_okx_service)):
    """Get current balance and assets"""
    try:
        balance = okx_service.get_balance()
        return balance
    except Exception as e:
        logger.error(f"Error fetching balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trade/{symbol}/{signal}")
async def trade(
    symbol: str,
    signal: str,
    strategy_service: StrategyService = Depends(get_strategy_service),
):
    """Execute trade based on RSI signal"""
    try:
        # Fiyat ve RSI değerlerini al
        ticker = strategy_service.okx.get_tickers().get(symbol)
        if not ticker:
            raise HTTPException(status_code=404, detail="Symbol not found")

        price = float(ticker["last"])
        rsi = strategy_service.calculate_rsi([price])

        # Al-sat işlemini gerçekleştir
        await strategy_service.execute_signal(symbol, signal, price)
        return {
            "status": "success",
            "symbol": symbol,
            "signal": signal,
            "price": price,
            "rsi": rsi,
        }
    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))
