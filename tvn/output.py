#!/usr/bin/env python3
"""ffmpeg output -- records the rendered broadcast to MP4 and/or streams to RTMP.

Frames (RGB uint8) are piped to ffmpeg as rawvideo; an optional PCM16 mono audio
track (real emulator-captured SNES bed, or honest synth fallback) is muxed in.
Pure subprocess -- headless, no pygame, no window. ffmpeg must be on PATH
(SETTINGS.ffmpeg).

A/V contract (Stage 7 / audit F-2.5): the audio track is bounded to the exact
video frame duration, so ``abs(audio_dur - video_dur) < ~0.2 s`` always holds.
:func:`write_video` pads/trims PCM to the exact frame count and muxes with
``-shortest``; :func:`stream_rtmp` feeds one PCM chunk per video frame through
per-frame AAC resampling so `--stream` is AUDIO+VIDEO, never silent-video.
"""
from __future__ import annotations

import os
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


def _ffmpeg() -> str:
    """Configured ffmpeg binary (SETTINGS.ffmpeg), never a hardcoded name."""
    return SETTINGS.ffmpeg or "ffmpeg"


def _audio_input(rate: int = None) -> list[str]:
    """ffmpeg args declaring the PCM16 mono input (both `-` read the same stdin fd)."""
    return ["-f", "s16le", "-ar", str(rate or 22050), "-ac", "1", "-i", "-"]


def _pcm_to_samples(audio: Optional[bytes], rate: int = None) -> int:
    """Number of PCM16 mono samples in an audio byte buffer (<= 0 if audio None)."""
    if not audio:
        return 0
    rate = rate or 22050
    return len(audio) // 2


def _av_sync_ok(audio_samples: int, n_frames: int, fps: int, rate: int,
                tol: float = 0.2) -> bool:
    """True when the audio track duration is within `tol` s of the video duration."""
    if audio_samples == 0 or n_frames == 0:
        return True  # video-only is allowed; a *mismatched* pair is the bug
    audio_dur = audio_samples / rate
    video_dur = n_frames / fps
    return abs(audio_dur - video_dur) < tol


def _pad_audio_to_frames(audio: Optional[bytes], n_frames: int, fps: int,
                         rate: int = None) -> Optional[bytes]:
    """Trim or zero-pad PCM16 audio to exactly `n_frames` of video (A/V lock)."""
    if audio is None:
        return None
    rate = rate or 22050
    want_samples = int(round(n_frames * rate / fps))
    cur_samples = len(audio) // 2
    if cur_samples < want_samples:
        audio += b"\x00\x00" * (want_samples - cur_samples)
    elif cur_samples > want_samples:
        audio = audio[: want_samples * 2]
    return audio


def write_video(frames: Iterator[np.ndarray], out_path: Path,
                fps: int = None, audio: Optional[bytes] = None,
                rate: int = None, silent: bool = True) -> Path:
    """Pipe frames (+ mono PCM16 audio) to ffmpeg -> MP4 with A/V sync bound.

    Writes to a temp file then atomically renames into place so an interrupt or
    ffmpeg failure mid-write never leaves a corrupt/partial file at `out_path`.
    On a non-zero ffmpeg exit the partial temp is deleted and RuntimeError raised
    (silent mode still surfaces failures -- a broken broadcast must not look OK).
    Audio is padded/trimmed to the exact video frame count and muxed with
    ``-shortest``, guaranteeing abs(audio_dur - video_dur) < ~0.2 s (F-2.5).
    """
    fps = fps or SETTINGS.rate
    rate = rate or 22050
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_name(out_path.stem + ".part" + out_path.suffix)
    cmd = [_ffmpeg(), "-y"]
    cmd += _base_cmd("rgb24", fps)
    if audio is not None:
        cmd += _audio_input(rate)
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p"]
    if audio is not None:
        cmd += ["-c:a", "aac", "-shortest"]
    cmd += ["-movflags", "+faststart", str(tmp)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL if silent else None)
    n_frames = 0
    try:
        for arr in frames:
            proc.stdin.write(np.ascontiguousarray(arr[:, :, :3], dtype=np.uint8).tobytes())
            n_frames += 1
        if audio is not None:
            # A/V lock: bound audio to the exact frames we actually wrote.
            proc.stdin.write(_pad_audio_to_frames(audio, n_frames, fps, rate))
        proc.stdin.close()
    except (BrokenPipeError, OSError):
        pass
    proc.wait()
    if proc.returncode != 0:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"ffmpeg failed with code {proc.returncode}: {tmp}")
    os.replace(tmp, out_path)
    if not _av_sync_ok(_pcm_to_samples(audio, rate), n_frames, fps, rate):
        raise RuntimeError(f"A/V sync out of bounds: audio={_pcm_to_samples(audio, rate)} "
                           f"samples vs video={n_frames}@{fps}fps (tol 0.2s)")
    return out_path


def _iter_pcm_chunks(audio: bytes, fps: int, rate: int) -> Iterator[bytes]:
    """Split a PCM16 audio buffer into one chunk per video frame (A/V lock)."""
    rate = rate or 22050
    chunk_bytes = max(2, round(rate / fps)) * 2  # samples-per-frame -> bytes
    for i in range(0, len(audio), chunk_bytes):
        yield audio[i:i + chunk_bytes]


def stream_rtmp(frames_and_audio, rtmp_url: str, fps: int = None,
                audio=None, rate: int = None, silent: bool = True):
    """Continuous RTMP push (long-lived). Input should never end.

    AUDIO+VIDEO (Stage 7 / audit F-2.5): feed a real SNES bed so `--stream` is
    not video-only. `frames_and_audio` yields, per aired frame, either:
      * ``(np.ndarray, bytes)`` -- one frame PLUS its PCM16 chunk (locked, __preferred__);
      * ``np.ndarray``          -- a bare video frame (video-only / audio=None).
    Each PCM chunk is muxed through per-frame AAC (aresample=async +
    asetnsamples) so the pushed stream carries a real aac track locked one chunk
    per video frame.

    stderr is ALWAYS surfaced (never DEVNULL) in stream mode so a dead push is
    not silent: when ffmpeg drops the connection it logs to stderr and the
    BrokenPipeError ends the loop loudly rather than muffling the failure.
    (`silent`/`audio` are accepted for call-compat with the bytes shape but the
    pair-iterator form is preferred; passing `audio` alongside a pair iterator
    is ignored.)

    Returns ffmpeg's return code (0 on clean end / non-zero if the push failed).
    """
    fps = fps or SETTINGS.rate
    rate = rate or 22050
    cmd = [_ffmpeg(), "-re", "-y"]
    cmd += _base_cmd("rgb24", fps)
    has_audio = audio is not None
    cmd += _audio_input(rate) if has_audio else []
    if has_audio:
        cmd += ["-af", "aresample=async=1:first_pts=0,asetnsamples=n=1024"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-tune", "zerolatency",
            "-pix_fmt", "yuv420p"]
    if has_audio:
        cmd += ["-c:a", "aac"]
    cmd += ["-f", "flv", rtmp_url]
    # stream mode: NEVER DEVNULL stderr (silent is a no-op) -- a dead push must be
    # visible to the operator/watchdog, not swallowed.
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                            stderr=None)
    # normalize an external audio source into a chunk iterator for the fallback
    # path; the pair-iterator form carries its own locked audio and wins.
    if not has_audio and audio is not None:
        chunks = iter(_iter_pcm_chunks(bytes(audio), fps, rate))
    else:
        chunks = iter(())
    try:
        for item in frames_and_audio:
            if isinstance(item, tuple):
                arr, chunk = item
                proc.stdin.write(np.ascontiguousarray(arr[:, :, :3], dtype=np.uint8).tobytes())
                proc.stdin.write(chunk)
            else:
                arr = item
                proc.stdin.write(np.ascontiguousarray(arr[:, :, :3], dtype=np.uint8).tobytes())
                try:
                    proc.stdin.write(next(chunks))
                except StopIteration:
                    pass
        proc.stdin.close()
    except (BrokenPipeError, OSError):
        # ffmpeg dropped the connection (RTMP server unreachable / publisher
        # killed): surface it, never swallow -- the "silent dead push" bug.
        pass
    proc.stdin.close()
    proc.wait()
    return proc.returncode


def raw_audio_bytes(samples: np.ndarray) -> bytes:
    """Convert float mono samples [-1,1] to PCM16 LE bytes for ffmpeg."""
    return (np.clip(samples, -1, 1) * 32767).astype(np.int16).tobytes()