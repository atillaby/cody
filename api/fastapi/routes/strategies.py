from fastapi import APIRouter

router = APIRouter(prefix="/strategies", tags=["Strategies"])


@router.get("/")
async def get_strategies():
    return {
        "active_strategies": 71,
        "performance_metrics": True,
        "dynamic_loading": True,
    }
