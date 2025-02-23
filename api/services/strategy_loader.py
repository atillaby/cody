import importlib
import logging
import os
from typing import Dict, Type

logger = logging.getLogger(__name__)


def load_strategies(strategy_folder: str) -> Dict[str, Type]:
    strategies = {}
    for filename in os.listdir(strategy_folder):
        if filename.endswith("_strategy.py"):
            module_name = filename[:-3]
            module_path = f"strategies.{module_name}"
            try:
                module = importlib.import_module(module_path)
                strategy_class = getattr(module, "Strategy")
                strategies[module_name] = strategy_class
                logger.info(f"Loaded strategy: {module_name}")
            except Exception as e:
                logger.error(f"Failed to load strategy {module_name}: {e}")
    return strategies
