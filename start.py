import logging
import os
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add project root to Python path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

if __name__ == "__main__":
    try:
        import uvicorn

        logger.info("Starting API server...")
        uvicorn.run(
            "api.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=[str(ROOT_DIR)],
            log_level="info",
            workers=1,
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)
