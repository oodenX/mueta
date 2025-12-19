# src/mueta/core/logging.py
import sys
from pathlib import Path
from loguru import logger

BASE_DIR = Path(__file__).resolve().parents[3]
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE_PATH = LOG_DIR / "app_{time:YYYY-MM-DD}.log"

def setup_logging(debug: bool = False):
    logger.remove()

    # Output to the terminal only in debug mode
    if debug:
        logger.add(
            sys.stderr,
            level="DEBUG"
        )

    logger.add(
        LOG_FILE_PATH,
        rotation="00:00",
        retention="15 days",
        compression="zip",
        encoding="utf-8",
        enqueue=True,
        level="INFO"
    )

    logger.info("Logging initialized.")
