import asyncio
import logging
import os

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)


class Database:
    client: AsyncIOMotorClient = None
    db = None

    @classmethod
    async def connect_db(cls):
        """MongoDB bağlantısını kur ve test et"""
        retries = 5
        while retries > 0:
            try:
                # MongoDB bağlantı string'ini environment'dan al veya default kullan
                connection_string = os.getenv(
                    "MONGODB_URI",
                    "mongodb://admin:admin123@mongodb:27017/trading_bot?authSource=admin&directConnection=true",
                )

                logger.info(
                    f"Trying to connect to MongoDB... (Attempts left: {retries})"
                )
                cls.client = AsyncIOMotorClient(
                    connection_string,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=5000,
                    socketTimeoutMS=5000,
                    maxPoolSize=10,  # Reduced from 50
                    minPoolSize=5,
                    maxIdleTimeMS=30000,
                )

                # Bağlantıyı test et
                await cls.client.admin.command("ping")
                cls.db = cls.client.trading_bot

                logger.info("Successfully connected to MongoDB")
                await cls.ensure_indexes()
                return cls.client

            except Exception as e:
                retries -= 1
                logger.error(f"MongoDB connection error: {e}")
                if retries > 0:
                    logger.info(f"Retrying in 5 seconds... ({retries} attempts left)")
                    await asyncio.sleep(5)
                else:
                    logger.error("Failed to connect to MongoDB after all retries")
                    raise

    @classmethod
    async def close_db(cls):
        if cls.client:
            cls.client.close()
            cls.client = None
            cls.db = None
            logger.info("MongoDB connection closed")

    @classmethod
    def get_db(cls):
        if not cls.db:
            raise ConnectionError("Database not initialized")
        return cls.db

    @classmethod
    async def ensure_indexes(cls):
        """Gerekli indeksleri oluştur"""
        if cls.db:
            try:
                await cls.db.signals.create_index([("timestamp", -1)])
                await cls.db.trades.create_index([("symbol", 1), ("timestamp", -1)])
                logger.info("MongoDB indexes created successfully")
            except Exception as e:
                logger.error(f"Error creating indexes: {e}")
