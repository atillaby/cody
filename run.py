import logging
import os
import socket
import sys
from pathlib import Path

import uvicorn

# Configure logging
log_file_path = Path(__file__).resolve().parent / "logs" / "app.log"
log_file_path.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file_path), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Add project root to Python path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))


def is_port_available(port: int) -> bool:
    """Check if a port is available"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("0.0.0.0", port))
            return True
        except:
            return False


def main():
    """Start the FastAPI server"""
    port = 8000

    # Check if port is available, if not, use an alternative port
    if not is_port_available(port):
        logger.warning(f"Port {port} is already in use! Trying port 8001...")
        port = 8001
        if not is_port_available(port):
            logger.error(f"Port 8001 is also in use! Exiting...")
            sys.exit(1)

    logger.info(f"Starting API server on port {port}...")
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        access_log=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
