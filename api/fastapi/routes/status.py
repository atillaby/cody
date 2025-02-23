from fastapi import APIRouter

router = APIRouter(prefix="/status", tags=["Status"])


@router.get("/")
async def get_status():
    return {
        "trading": True,
        "active_pairs": 20,
        "total_strategies": 71,
        "current_balance": "USDT",
    }
