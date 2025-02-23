import logging
from typing import Dict

import aioredis
import motor.motor_asyncio
from prometheus_client import CollectorRegistry, Gauge

logger = logging.getLogger(__name__)


class HealthCheck:
    def __init__(self):
        self.registry = CollectorRegistry()
        self.service_status = Gauge(
            "service_status",
            "Service Health Status",
            ["service"],
            registry=self.registry,
        )

    async def check_redis(self, redis_client) -> Dict:
        try:
            await redis_client.ping()
            self.service_status.labels(service="redis").set(1)
            return {"status": "ok"}
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            self.service_status.labels(service="redis").set(0)
            return {"status": "error", "message": str(e)}

    async def check_mongodb(self, mongo_client) -> Dict:
        try:
            await mongo_client.admin.command("ping")
            self.service_status.labels(service="mongodb").set(1)
            return {"status": "ok"}
        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            self.service_status.labels(service="mongodb").set(0)
            return {"status": "error", "message": str(e)}

    async def check_all_services(self, redis_client, mongo_client) -> Dict:
        redis_status = await self.check_redis(redis_client)
        mongo_status = await self.check_mongodb(mongo_client)

        return {
            "redis": redis_status,
            "mongodb": mongo_status,
            "status": "ok"
            if all(s["status"] == "ok" for s in [redis_status, mongo_status])
            else "error",
        }
