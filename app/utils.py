from pathlib import Path
import logging

ROOT_DIR = Path(__file__).parent.parent
LOG_LEVEL = "INFO"

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

__all__ = ["ROOT_DIR", "logger"]
