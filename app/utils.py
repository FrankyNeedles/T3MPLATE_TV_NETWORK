from pathlib import Path
import logging

ROOT_DIR = Path(__file__).resolve().parent.parent
LOG_LEVEL = "INFO"

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

log_dir = ROOT_DIR / "logs"
log_dir.mkdir(exist_ok=True)
handler = logging.FileHandler(log_dir / "tv_network.log")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

__all__ = ["ROOT_DIR", "logger"]
