import logging
from decimal import Decimal
from typing import Dict

import ccxt
import requests

import redis

from ..config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OKXService:
    def __init__(self):
        try:
            self.settings = get_settings()
            # Redis bağlantısını güvenli şekilde kur
            self.redis_client = redis.Redis(
                host="redis",
                port=6379,
                db=0,
                password="admin123",
                ssl=False,
                decode_responses=True,
            )
            logger.info("Connected to Redis securely")

            # Önce IP adresini kontrol et
            self.current_ip = self.get_current_ip()
            logger.info(f"Current IP Address: {self.current_ip}")

            self.exchange = ccxt.okx(
                {
                    "apiKey": self.settings.OKX_API_KEY,
                    "secret": self.settings.OKX_SECRET_KEY,
                    "password": self.settings.OKX_PASSPHRASE,
                    "enableRateLimit": True,
                    "options": {"defaultType": "spot", "adjustForTimeDifference": True},
                }
            )
            logger.info("OKX exchange instance created successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OKX service: {e}")
            raise
        logger.info("OKX service initialized")

    def get_current_ip(self) -> str:
        try:
            response = requests.get("https://api.ipify.org?format=json")
            ip = response.json()["ip"]
            logger.info(f"Detected IP: {ip}")
            return ip
        except Exception as e:
            logger.error(f"Failed to get IP address: {e}")
            return "Unknown"

    def get_tickers(self):
        try:
            logger.info("Fetching tickers...")
            tickers = self.exchange.fetch_tickers()
            logger.info(f"Found {len(tickers)} tickers")
            for symbol, ticker in list(tickers.items())[:5]:
                logger.info(f"Sample ticker - {symbol}: {ticker['last']}")
            # Ticker verilerini Redis'e yaz
            self.redis_client.set("tickers", str(tickers))
            return tickers
        except Exception as e:
            logger.error(f"Error fetching tickers: {str(e)}")
            return {"error": str(e)}

    def get_balance(self) -> Dict:
        try:
            logger.info("Fetching balance...")
            balance = self.exchange.fetch_balance()
            logger.info(f"Balance fetched: {balance}")
            return balance
        except Exception as e:
            logger.error(f"Failed to fetch balance: {e}")
            return {"status": "error", "message": str(e)}

    def place_market_order(self, symbol: str, side: str, amount: Decimal) -> Dict:
        """Execute real market order on OKX"""
        try:
            logger.info(f"Placing {side} market order: {amount} {symbol}")

            # Market emri oluştur
            order = self.exchange.create_market_order(symbol, side, float(amount))
            logger.info(f"Market order placed: {order}")

            # Tüm order detaylarını döndür
            return order

        except Exception as e:
            logger.error(f"Failed to place market order: {e}")
            return {"status": "error", "message": str(e)}

    def test_connection(self):
        try:
            logger.info(f"Testing OKX connection from IP: {self.current_ip}")
            # Önce basit bir API çağrısı yap
            status = self.exchange.fetch_status()
            if status["status"] == "ok":
                logger.info("Basic API connection successful")

            # Market verilerini kontrol et
            markets = self.exchange.load_markets()
            logger.info(f"Successfully loaded {len(markets)} markets")

            return {
                "status": "connected",
                "ip": self.current_ip,
                "markets_count": len(markets),
                "server_time": self.exchange.fetch_time(),
            }
        except Exception as e:
            error_msg = str(e)
            if "IP whitelist" in error_msg:
                logger.error(
                    f"IP whitelist error. Current IP ({self.current_ip}) needs to be added to OKX API settings"
                )
                return {
                    "status": "error",
                    "type": "ip_whitelist",
                    "current_ip": self.current_ip,
                    "message": "Please add this IP to your OKX API whitelist",
                }
            logger.error(f"Connection test failed: {error_msg}")
            return {"status": "error", "message": error_msg}

    def test_redis_connection(self):
        try:
            self.redis_client.ping()
            logger.info("Redis connection successful")
            return True
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            return False

    def get_balances(self):
        try:
            balances = self.exchange.fetch_balance()
            logger.info(f"Fetched balances: {balances}")
            return balances
        except Exception as e:
            logger.error(f"Error fetching balances: {str(e)}")
            return None

    def get_top_pairs(self, limit=20):
        try:
            tickers = self.get_tickers()
            sorted_tickers = sorted(
                tickers.items(), key=lambda x: x[1]["quoteVolume"], reverse=True
            )
            top_pairs = sorted_tickers[:limit]
            logger.info(f"Top {limit} pairs: {top_pairs}")
            # En iyi çiftleri Redis'e yaz
            self.redis_client.set("top_pairs", str(top_pairs))
            return top_pairs
        except Exception as e:
            logger.error(f"Error fetching top pairs: {str(e)}")
            return None

    def get_trading_limits(self):
        try:
            logger.info("Fetching trading limits...")
            markets = self.exchange.load_markets()
            trading_limits = {
                symbol: market["limits"] for symbol, market in markets.items()
            }
            logger.info(f"Fetched trading limits for {len(trading_limits)} pairs")

            # Trading limitleri string'e çevir ve Redis'e yaz
            trading_limits_str = str(trading_limits)
            self.redis_client.set("trading_limits", trading_limits_str)

            return trading_limits
        except Exception as e:
            logger.error(f"Error fetching trading limits: {str(e)}")
            return None
