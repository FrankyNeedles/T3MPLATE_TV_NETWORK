#!/usr/bin/env python3
"""Stage 7 RTMP gate driver: push a short real broadcast (audio+video) to a
local RTMP server, so we can ffprobe the pushed endpoint for both streams.

Usage:
    python scripts/_stage7_rtmp_ping.py rtmp://localhost:1935/test [--seconds 6]
The script is infinite-loop-safe bounded: it pushes a fixed number of segments
then closes stdin cleanly (stream_rtmp returns), letting the test finish.
"""
import argparse
import sys

from tvn import audio, output, runner, gary, programming, renderer
from tvn.config import SETTINGS
from tvn.world import open_world


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("url", help="full rtmp://host/app/key endpoint")
    ap.add_argument("--seconds", type=float, default=8.0, help="seconds per segment")
    ap.add_argument("--segments", type=int, default=3, help="how many segments to push")
    args = ap.parse_args()
    world = open_world()
    g = gary.GaryPD(world)
    fps = SETTINGS.rate
    rate = audio.RATE
    chunk_cyc = max(2, round(rate / fps)) * 2

    def bounded_av():
        """Push `--segments` rendered segments as locked (frame, chunk) pairs."""
        pushed = 0
        seed = 1000
        while pushed < args.segments:
            slot = programming.get_slot()
            seg = g.decide(slot, seed=seed + pushed)
            world.on_air([c.name for c in seg.cast], show=seg.title,
                         tension=2 if seg.daypart in ("prime", "access") else 0)
            rr = renderer.Renderer()
            frames = runner.segment_frames(seg, seconds=args.seconds, renderer_=rr)
            pcm = output.raw_audio_bytes(audio.mixer.track_for(
                seg.fmt, args.seconds, variant=pushed))
            n = 0
            for i, arr in enumerate(frames):
                chunk = pcm[i * chunk_cyc:][:chunk_cyc]
                if not chunk:
                    chunk = b"\x00\x00" * (chunk_cyc // 2)
                yield arr, chunk
                n += 1
            pushed += 1
            print(f"[ping] segment {pushed} rendered {n} frames (fmt={seg.fmt})",
                  flush=True)

    print(f"[ping] pushing audio+video to {args.url} ...")
    rc = output.stream_rtmp(bounded_av(), args.url)
    print(f"[ping] stream_rtmp returned code {rc}", flush=True)
    return rc if rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
