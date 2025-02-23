import asyncio
import logging
from typing import Dict, List, Callable
from datetime import datetime

logger = logging.getLogger(__name__)

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, asyncio.Task] = {}
        self.schedules: Dict[str, int] = {}
        self._running = True

    async def add_task(self, name: str, coro: Callable, interval: int = 60):
        """Yeni bir task ekle"""
        if name in self.tasks:
            logger.warning(f"Task {name} already exists, stopping old task")
            await self.stop_task(name)

        self.schedules[name] = interval
        self.tasks[name] = asyncio.create_task(self._run_task(name, coro))
        logger.info(f"Added task: {name} with interval {interval}s")

    async def _run_task(self, name: str, coro: Callable):
        """Task'ı periyodik olarak çalıştır"""
        while self._running:
            try:
                start_time = datetime.now()
                await coro()
                duration = (datetime.now() - start_time).total_seconds()
                logger.debug(f"Task {name} completed in {duration:.2f}s")

                # Bir sonraki çalışma için bekle
                await asyncio.sleep(self.schedules[name])
            except Exception as e:
                logger.error(f"Error in task {name}: {e}")
                await asyncio.sleep(5)  # Hata durumunda kısa bekle

    async def stop_task(self, name: str):
        """Belirtilen task'ı durdur"""
        if name in self.tasks:
            self.tasks[name].cancel()
            del self.tasks[name]
            logger.info(f"Stopped task: {name}")

    async def stop_all(self):
        """Tüm taskları durdur"""
        self._running = False
        for name in list(self.tasks.keys()):
            await self.stop_task(name)
        logger.info("All tasks stopped")

    def get_task_status(self) -> List[Dict]:
        """Tüm taskların durumunu getir"""
        return [
            {
                "name": name,
                "running": not task.done(),
                "interval": self.schedules.get(name, 0),
                "last_error": str(task.exception()) if task.done() and task.exception() else None
            }
            for name, task in self.tasks.items()
        ]
