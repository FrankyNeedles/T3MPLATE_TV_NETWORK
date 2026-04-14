from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path
import os


class Config(BaseSettings):
    """Project configuration."""

    project_name: str = "T3MPLATE_TV_NETWORK"
    project_root: Path = Path(__file__).parent.parent

    # Paths
    assets_dir: Path = project_root / "assets"
    roms_dir: Path = assets_dir / "roms"
    data_dir: Path = project_root / "data"
    engine_dir: Path = project_root / "engine"

    # API
    api_host: str = "localhost"
    api_port: int = 8080
    dev_mode: bool = Field(default=False, env="DEV_MODE")
    api_reload: bool = dev_mode

    # AI
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY")
    gary_model: str = "x-ai/grok-4-fast"

    # Extraction
    top_games_count: int = 50
    tcrf_base_url: str = "https://datacrystal.tcrf.net/wiki"

    # Audio/Visual
    frame_rate: int = 60
    audio_channels: int = 8

    class Config:
        env_file = ".env"


CONFIG = Config()
