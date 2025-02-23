import json
import logging
from typing import Any, Optional
from datetime import datetime, timedelta

import redis

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.default_ttl = 300  # 5 dakika

    async def get(self, key: str) -> Optional[Any]:
        """Cache'den veri getir"""
        try:
            data = self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Cache get error for {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Cache'e veri kaydet"""
        try:
            json_data = json.dumps(value)
            return self.redis.set(
                key,
                json_data,
                ex=ttl if ttl else self.default_ttl
            )
        except Exception as e:
            logger.error(f"Cache set error for {key}: {e}")
            return False

    async def invalidate(self, pattern: str = None):
        """Cache'i temizle"""
        try:
            if pattern:
                keys = self.redis.keys(pattern)
                if keys:
                    self.redis.delete(*keys)
            else:
                self.redis.flushdb()
            logger.info(f"Cache invalidated for pattern: {pattern or 'all'}")
            return True
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return False

    async def get_stats(self) -> dict:
        """Cache istatistiklerini getir"""
        try:
            info = self.redis.info()
            return {
                "used_memory": info["used_memory_human"],
                "connected_clients": info["connected_clients"],
                "total_keys": len(self.redis.keys("*")),
                "last_save": datetime.fromtimestamp(info["rdb_last_save_time"]).isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
