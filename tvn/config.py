#!/usr/bin/env python3
"""Central configuration for the T3MPLATE TV runtime.

All paths resolve relative to the repo root (from this file), never CWD,
so the broadcast is portable and can run 24/7 from any working directory.
"""
from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - tolerate environments without dotenv
    load_dotenv = None

ROOT = Path(__file__).resolve().parent.parent

if load_dotenv is not None:
    # `.env` at repo root (TWITCH_STREAM_KEY, T3TV_FFMPEG, ...) must be loaded
    # BEFORE Settings reads os.getenv, or --stream/.env config is dead on arrival.
    load_dotenv(ROOT / ".env")


class Settings:
    """Runtime settings. Environment-driven, with portable path defaults."""

    def __init__(self, root: Path = ROOT):
        self.root = root
        self.data_dir = root / "data"
        self.output_dir = root / "OUTPUT"
        self.lore_dir = self.data_dir / "lore"
        self.recordings_dir = self.output_dir / "recordings"
        self.broadcast_dir = self.output_dir / "broadcast"
        self.db_path = self.lore_dir / "living_world.db"
        self.asset_catalog_path = root / "assets" / "catalog.json"

        # A/V
        self.rate = 24          # fps for rendered output (SNES-era broadcast cadence)
        self.res_native = (256, 224)   # SNES native framebuffer
        self.scale = 2          # integer upscale to 512x448 (SNES-faithful, no blur)

        # Streaming
        self.twitch_stream_key = os.getenv("TWITCH_STREAM_KEY", "")
        self.rtmp_url = (
            f"rtmp://live.twitch.tv/app/{self.twitch_stream_key}"
            if self.twitch_stream_key
            else ""
        )
        self.ffmpeg = os.getenv("T3TV_FFMPEG", "ffmpeg")

        self.ensure_dirs()

    def ensure_dirs(self) -> None:
        for d in (self.data_dir, self.lore_dir, self.output_dir,
                  self.recordings_dir, self.broadcast_dir):
            d.mkdir(parents=True, exist_ok=True)

    @property
    def resolution(self) -> tuple[int, int]:
        w, h = self.res_native
        return w * self.scale, h * self.scale


SETTINGS = Settings()