#!/usr/bin/env python3
"""ffmpeg output -- records the rendered broadcast to MP4 and/or streams to RTMP.

Frames (RGB uint8) are piped to ffmpeg as rawvideo; an optional PCM16 mono audio
track (synthesized SNES bed, or a real SPC render) is muxed in. Pure subprocess --
headless, no pygame, no window. ffmpeg must be on PATH (SETTINGS.ffmpeg).
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterator, Optional

import numpy as np

from .config import SETTINGS


def _res() -> str:
    w, h = SETTINGS.resolution
    return f"{w}x{h}"


def _base_cmd(pix: str = "rgb24", rate: int = None):
    rate = rate or SETTINGS.rate
    return ["-f", "rawvideo", "-pix_fmt", pix, "-s", _res(), "-r", str(rate), "-i", "-"]


def write_video(frames: Iterator[np.ndarray], out_path: Path,
                fps: int = None, audio: Optional[bytes] = None,
                rate: int = None, silent: bool = True) -> Path:
    """Pipe frames (+ optional mono PCM16 audio bytes) to ffmpeg -> MP4."""
    fps = fps or SETTINGS.rate
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y"]
    cmd += _base_cmd("rgb24", fps)
    in_pipes = 1
    if audio is not None:
        cmd += ["-f", "s16le", "-ar", str(rate or 22050), "-ac", "1", "-i", "-"]
        in_pipes += 1
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-movflags", "+faststart", str(out_path)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL if silent else None)
    try:
        for arr in frames:
            proc.stdin.write(np.ascontiguousarray(arr[:, :, :3], dtype=np.uint8).tobytes())
        if audio is not None:
            proc.stdin.write(audio)
        proc.stdin.close()
    except (BrokenPipeError, OSError):
        pass
    proc.wait()
    if proc.returncode != 0 and not silent:
        raise RuntimeError(f"ffmpeg failed with code {proc.returncode}: {out_path}")
    return out_path


def stream_rtmp(frames: Iterator[np.ndarray], rtmp_url: str, fps: int = None,
                audio: Optional[bytes] = None, rate: int = None,
                silent: bool = False):
    """Continuous RTMP push (long-lived). `frames` should never end."""
    fps = fps or SETTINGS.rate
    cmd = ["ffmpeg", "-re", "-y"]
    cmd += _base_cmd("rgb24", fps)
    in_pipes = 1
    if audio is not None:
        cmd += ["-f", "s16le", "-ar", str(rate or 22050), "-ac", "1", "-i", "-"]
        in_pipes += 1
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-tune", "zerolatency",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-f", "flv", rtmp_url]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL if silent else None)
    try:
        for arr in frames:
            proc.stdin.write(np.ascontiguousarray(arr[:, :, :3], dtype=np.uint8).tobytes())
            if audio is not None:
                proc.stdin.write(audio)
    except (BrokenPipeError, OSError):
        pass
    proc.stdin.close()
    proc.wait()
    return proc.returncode


def raw_audio_bytes(samples: np.ndarray) -> bytes:
    """Convert float mono samples [-1,1] to PCM16 LE bytes for ffmpeg."""
    return (np.clip(samples, -1, 1) * 32767).astype(np.int16).tobytes()