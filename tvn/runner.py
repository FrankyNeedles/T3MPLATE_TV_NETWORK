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
from .broadcast import BroadcastSegment
from .config import SETTINGS
from .world import open_world


def make_world():
    return open_world()


def segment_frames(seg, fps: int = None, seconds: Optional[float] = None,
                   renderer_=None) -> Iterator[np.ndarray]:
    """Yield renderer frames for a segment, cycled to fill `seconds` (or one pass).

    `seconds=None` -> a single render pass of the segment. An explicit
    non-positive `seconds` (e.g. `--seconds 0`) is bounded to one pass -- it
    must NEVER become an infinite loop (falsy-0 bug).
    """
    fps = fps or SETTINGS.rate
    r = renderer_ or renderer.Renderer()
    # (M1) an EXPLICIT non-positive duration is a bounded no-op -- never a
    # `total=None` continuous/infinite generator. `None` stays "until stopped".
    if seconds is not None and seconds <= 0:
        return
    total = None if seconds is None else int(seconds * fps)
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
                 tension=2 if seg.daypart in ("prime", "access") else 0,
                 genre=seg.fmt)
    out = out or (SETTINGS.recordings_dir / f"{seg.seg_id}.mp4")
    center = renderer.Renderer()
    frames = segment_frames(seg, seconds=seconds, renderer_=center)
    a = segment_audio(seg, seconds)
    output.write_video(frames, out, audio=a)
    return out


_last_tick_ts: Optional[float] = None
# per-airing seed counter (GAP-3): every pass mints a fresh seed so the next
# chunk is NOT byte-identical to the last, even in the same grid slot.
_pass_counter = 0
# last aired dialogue signature (guards CONSECUTIVE chunks from byte-identity)
_last_beats: Optional[tuple[str, ...]] = None


def _next_seed() -> int:
    global _pass_counter
    _pass_counter += 1
    return int(time.time() * 1000) + _pass_counter


def _decide_differing(g, slot, base_seed: int) -> BroadcastSegment:
    """Decide a segment whose dialogue differs from the previously aired one, so
    consecutive airings are never byte-identical (GAP-3). Bounded: if every seed
    in a small window collides, accept the last (never infinite)."""
    global _last_beats
    chosen = None
    for i in range(8):
        seg = g.decide(slot, seed=base_seed + i)
        beats = getattr(seg, "beats", [])
        sig = tuple(b.text for b in beats)
        if _last_beats is None or sig != _last_beats:
            chosen = seg
            break
        chosen = seg
    beats = getattr(chosen, "beats", [])
    _last_beats = tuple(b.text for b in beats)
    return chosen


def _record_cycle(world, g, out_dir: Path, seconds: float = 12.0) -> Path:
    seed = _next_seed()
    slot = programming.get_slot()
    seg = _decide_differing(g, slot, seed)
    world.on_air([c.name for c in seg.cast], show=seg.title,
                 tension=2 if seg.daypart in ("prime", "access") else 0,
                 genre=seg.fmt)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = out_dir / f"{stamp}_{slot.fmt}.mp4"
    dur = seconds
    frames = segment_frames(seg, seconds=dur)
    a = segment_audio(seg, dur)
    output.write_video(frames, out, audio=a)
    return out


def run_forever(stream: bool = False, record_dir: Optional[Path] = None,
                world=None, seconds: float = 12.0):
    """24/7 loop: air one slot's segment, advance the world, repeat.

    Streams continuously to Twitch if SETTINGS.twitch_stream_key and stream=True,
    else records an append-only MP4 chunk per aired segment into OUTPUT/recordings/.
    `seconds` (sec/segment) is honored in both record and stream modes.
    """
    global _last_tick_ts
    world = world or make_world()
    g = gary.GaryPD(world)
    record_dir = record_dir or SETTINGS.recordings_dir
    record_dir.mkdir(parents=True, exist_ok=True)
    _last_tick_ts = None

    if stream and SETTINGS.rtmp_url:

        def frames_forever():
                    while True:
                        slot = programming.get_slot()
                        seg = g.decide(slot, seed=_next_seed())
                        world.on_air([c.name for c in seg.cast], show=seg.title,
                                     tension=2 if seg.daypart in ("prime", "access") else 0,
                                     genre=seg.fmt)
                        renderer_ = renderer.Renderer()
                        for arr in segment_frames(seg, seconds=seconds, renderer_=renderer_):
                            yield arr

        url_redacted = SETTINGS.rtmp_url.replace(SETTINGS.twitch_stream_key, "***")
        print(f"Streaming (video-only MVP) to {url_redacted} ...")
        output.stream_rtmp(frames_forever(), SETTINGS.rtmp_url, silent=False)
        return

    # record mode: 24/7 append-only MP4 chunks
    print(f"Recording broadcast chunks to {record_dir} (Ctrl+C to stop).")
    try:
        while True:
            path = _record_cycle(world, g, record_dir, seconds=seconds)
            print(f"[{datetime.now():%H:%M:%S}] airing -> {path.name}", flush=True)
            _maybe_tick(world)
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nBroadcast stopped.")


def _maybe_tick(world):
    """Hourly maintenance that NEVER blocks the render loop (Stage 4 / BUG-2).

    Runs world.tick() once per hour on a monotonic schedule regardless of the
    wall-clock hour. The old code gated on hours {2,3,4} -- a broadcaster that
    started at e.g. 9am could run for days without a single tick(), so decay /
    career / seeking-work evolution never happened. Now tick() is guaranteed
    roughly hourly from the moment the loop starts.
    """
    global _last_tick_ts
    now = time.monotonic()
    if _last_tick_ts is None or now - _last_tick_ts >= 3600:
        world.tick()
        _last_tick_ts = now