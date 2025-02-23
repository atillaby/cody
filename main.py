import asyncio
import logging
import socket
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from decimal import Decimal

from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Proje dizinini sys.path'e ekleyin
sys.path.append(str(Path(__file__).resolve().parent))

# Service imports
from api.config.database import Database
from api.routes import strategies_router, trading_router
from api.services import (
    OKXService, TelegramService, StrategyService,
    PortfolioManager, WebSocketService, TaskManager,
    CacheManager, MetricsService, PerformanceAnalyzer,
    RiskManager
)
from api.services.telegram_bot import TradingBot
from api.config.telegram_config import TelegramSettings

# Strategy imports
from strategies import (
    ADXStrategy, ATRStrategy, BollingerBandsStrategy,
    CCIStrategy, FibonacciStrategy, HeikenAshiStrategy,
    KeltnerChannelStrategy, MACDStrategy, RSIStrategy,
    TWAPStrategy, VWAPStrategy
)

# Logging setup
log_file_path = Path(__file__).resolve().parent / "logs" / "app.log"
log_file_path.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file_path), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Initialize services
def init_services():
    services = {
        'okx': OKXService(),
        'telegram': TelegramService()
    }

    services['strategy'] = StrategyService(services['okx'], services['telegram'])
    services['portfolio'] = PortfolioManager(services['okx'])
    services['websocket'] = WebSocketService()
    services['task'] = TaskManager()
    services['cache'] = CacheManager(redis_client=services['okx'].redis_client)
    services['metrics'] = MetricsService()
    services['performance'] = PerformanceAnalyzer(services['cache'], Database)
    services['risk'] = RiskManager()

    return services

# Initialize strategies
def init_strategies(okx_service, telegram_service):
    return [
        cls(okx_service, telegram_service) for cls in [
            ADXStrategy, ATRStrategy, BollingerBandsStrategy,
            CCIStrategy, FibonacciStrategy, HeikenAshiStrategy,
            KeltnerChannelStrategy, MACDStrategy, RSIStrategy,
            TWAPStrategy, VWAPStrategy
        ]
    ]

# Initialize services and strategies
services = init_services()
strategies = init_strategies(services['okx'], services['telegram'])

# Initialize Telegram bot
telegram_settings = TelegramSettings()
trading_bot = TradingBot(
    token=telegram_settings.BOT_TOKEN,
    strategy_service=services['strategy'],
    portfolio_manager=services['portfolio']
)

# Lifespan events
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting trading bot...")
    await Database.connect_db()

    # Start background tasks
    tasks = {
        "strategies": run_strategies,
        "monitoring": monitor_pairs,
        "portfolio": update_portfolio
    }

    for name, task in tasks.items():
        await services['task'].add_task(name, task)

    yield

    # Cleanup
    await Database.close_db()
    await services['task'].stop_all()
    logger.info("Trading bot stopped")

# FastAPI app setup
app = FastAPI(
    title="Trading Bot API",
    description="Crypto trading bot with multiple strategies",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add routers
app.include_router(strategies_router, prefix="/strategies", tags=["Strategies"])
app.include_router(trading_router, prefix="/trading", tags=["Trading"])

# Background tasks
async def run_strategies():
    """Strategy execution loop"""
    while True:
        for strategy in strategies:
            try:
                await strategy.check_signals("BTC/USDT")
            except Exception as e:
                logger.error(f"Strategy error {strategy.__class__.__name__}: {e}")
        await asyncio.sleep(60)

async def monitor_pairs():
    """Market monitoring loop"""
    while True:
        try:
            pairs = services['okx'].get_top_pairs()
            for pair, data in pairs:
                logger.info(f"Monitoring {pair}: Vol={data['quoteVolume']}, Price={data['last']}")
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
        await asyncio.sleep(900)

async def update_portfolio():
    """Portfolio update loop"""
    while True:
        try:
            services['portfolio'].update_portfolio()
            value = services['portfolio'].get_portfolio_value()
            logger.info(f"Portfolio Value: {value} USDT")
        except Exception as e:
            logger.error(f"Portfolio update error: {e}")
        await asyncio.sleep(60)

# API Endpoints
@app.get("/health")
async def health_check():
    """System health check"""
    checks = {
        "redis": await services['okx'].test_redis_connection(),
        "mongodb": await Database.get_db().command("ping"),
        "tasks": services['task'].get_task_status()
    }
    return {"status": "ok", "checks": checks}

@app.get("/metrics")
async def get_metrics():
    """System metrics"""
    return await services['metrics'].get_strategy_metrics("all")

@app.post("/validate_trade")
async def validate_trade(symbol: str, side: str, amount: float):
    """Trade validation"""
    portfolio_value = await services['portfolio'].get_portfolio_value()
    is_valid, message = await services['risk'].validate_trade(
        symbol, side, Decimal(str(amount)), Decimal(str(portfolio_value))
    )
    return {"valid": is_valid, "message": message}

# WebSocket endpoint
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket connection handler"""
    await services['websocket'].connect(client_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("action") == "subscribe" and "symbol" in data:
                await services['websocket'].subscribe_to_symbol(client_id, data["symbol"])
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await services['websocket'].disconnect(client_id, websocket)

# Add to startup event
@app.on_event("startup")
async def startup_event():
    # Start Telegram bot
    asyncio.create_task(trading_bot.run())
    logger.info("Telegram bot started")

# Main entry point
if __name__ == "__main__":
    import uvicorn
    port = 8000

    def find_available_port(start_port: int) -> int:
        """Find first available port starting from start_port"""
        for port in range(start_port, start_port + 3):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(("0.0.0.0", port))
                    return port
                except OSError:
                    continue
        raise RuntimeError("No available ports found")

    try:
        port = find_available_port(8000)
        logger.info(f"Starting server on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)
