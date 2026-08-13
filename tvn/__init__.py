#!/usr/bin/env python3
"""T3MPLATE TV WORLD - minimal honest MVP runtime.

A clean, self-contained, headless runtime for the core vision:
"the SNES world presented as a living 90s network TV broadcast, running 24/7."

Stack: Python 3.11/3.12, SQLAlchemy (world continuity), Pillow (headless render),
ffmpeg (record MP4 / optional RTMP to Twitch). NO pygame, NO sounddevice, NO window.
"""
__version__ = "0.1.0"