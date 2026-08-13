#!/usr/bin/env python3
"""Runner -- the loop that makes the broadcast LIVE.

Pipeline (wires world-state -> content -> render -> record, per RESEARCH_LIVING):
    living_world.tick() (maintenance)
      -> programming.get_slot()  (fixed 90s grid -> current show/format)
      -> gary.decide(slot)       (world-aware beat selector -> BroadcastSegment)
      -> renderer.render_segment (SNES dialogue + chrome + movement, Pillow)
      -> gary.world.on_air(...)  (CAUSAL feedback: co-hosts drift, ratings move)
      -> ffmpeg                  (record MP4 chunk and/or continuous RTMP)
"""
from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional

import numpy as np

from . import programming, gary, renderer, output, audio
from .config import SETTINGS
from .world import open_world


def make_world():
    return open_world()


def segment_frames(seg, fps: int = None, seconds: Optional[float] = None,
                   renderer_=None) -> Iterator[np.ndarray]:
    """Yield renderer frames for a segment, cycled to fill `seconds` (or one pass)."""
    fps = fps or SETTINGS.rate
    r = renderer_ or renderer.Renderer()
    total = int(seconds * fps) if seconds else None
    count = 0
    while total is None or count < total:
        for arr in renderer.render_segment(seg, final=True, renderer=r, fps=fps):
            yield arr
            count += 1
            if total is not None and count >= total:
                return


def segment_audio(seg, seconds: float, fmt: str = "") -> bytes:
    return output.raw_audio_bytes(audio.mixer.track_for(fmt or seg.fmt, seconds))


def run_once(seconds: float = 30.0, out: Optional[Path] = None,
             world=None, gary_=None) -> Path:
    """Record a single coherent broadcast segment (current grid slot) to MP4."""
    world = world or make_world()
    g = gary_ or gary.GaryPD(world)
    slot = programming.get_slot()
    seg = g.decide(slot)
    # causal feedback: co-hosts on this show drift + ratings move
    world.on_air([c.name for c in seg.cast], show=seg.title,
                 tension=2 if seg.daypart in ("prime", "access") else 0)
    out = out or (SETTINGS.recordings_dir / f"{seg.seg_id}.mp4")
    center = renderer.Renderer()
    frames = segment_frames(seg, seconds=seconds, renderer_=center)
    a = segment_audio(seg, seconds)
    output.write_video(frames, out, audio=a)
    return out


def _record_cycle(world, g, out_dir: Path) -> Path:
    slot = programming.get_slot()
    seg = g.decide(slot)
    world.on_air([c.name for c in seg.cast], show=seg.title,
                 tension=2 if seg.daypart in ("prime", "access") else 0)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = out_dir / f"{stamp}_{slot.fmt}.mp4"
    dur = 12.0
    frames = segment_frames(seg, seconds=dur)
    a = segment_audio(seg, dur)
    output.write_video(frames, out, audio=a)
    return out


def run_forever(stream: bool = False, record_dir: Optional[Path] = None,
                world=None):
    """24/7 loop: air one slot's segment, advance the world, repeat.

    Streams continuously to Twitch if SETTINGS.twitch_stream_key and stream=True,
    else records an append-only MP4 chunk per aired segment into OUTPUT/recordings/.
    """
    world = world or make_world()
    g = gary.GaryPD(world)
    record_dir = record_dir or SETTINGS.recordings_dir
    record_dir.mkdir(parents=True, exist_ok=True)

    if stream and SETTINGS.rtmp_url:

        def frames_forever():
            while True:
                slot = programming.get_slot()
                seg = g.decide(slot)
                world.on_air([c.name for c in seg.cast], show=seg.title,
                             tension=2 if seg.daypart in ("prime", "access") else 0)
                renderer_ = renderer.Renderer()
                for arr in segment_frames(seg, seconds=12.0, renderer_=renderer_):
                    yield arr

        url_redacted = SETTINGS.rtmp_url.replace(SETTINGS.twitch_stream_key, "***")
        print(f"Streaming (video-only MVP) to {url_redacted} ...")
        output.stream_rtmp(frames_forever(), SETTINGS.rtmp_url, silent=False)
        return

    # record mode: 24/7 append-only MP4 chunks
    print(f"Recording broadcast chunks to {record_dir} (Ctrl+C to stop).")
    try:
        while True:
            path = _record_cycle(world, g, record_dir)
            print(f"[{datetime.now():%H:%M:%S}] airing -> {path.name}", flush=True)
            _maybe_tick(world)
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nBroadcast stopped.")


def _maybe_tick(world):
    h = datetime.now().hour
    if h in (2, 3, 4):
        world.tick()
        time.sleep(3600)  # maintenance hourly