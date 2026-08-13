#!/usr/bin/env python3
"""T3MPLATE TV WORLD -- one-shot broadcast demo + world check.

Records a short real broadcast segment of the current grid slot (with SNES-style
audio) to OUTPUT/broadcast/demo.mp4, and prints the living-world digest + morning
report so you can see content is CAUSED by the world (not random).

Green-gate check: `ffprobe OUTPUT/broadcast/demo.mp4` should show a non-blank
512x448 h264 video stream + aac audio, length == the requested seconds.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tvn import runner
from tvn.config import SETTINGS
from tvn.world import open_world


def main() -> int:
    ap = argparse.ArgumentParser(description="T3MPLATE TV one-shot demo broadcast")
    ap.add_argument("--seconds", type=float, default=20.0, help="length (s)")
    ap.add_argument("--out", type=str, default=str(SETTINGS.broadcast_dir / "demo.mp4"))
    args = ap.parse_args()

    world = open_world()   # persistent DB under data/lore/
    print("=" * 64)
    print("T3MPLATE TV WORLD -- living 90s SNES broadcast")
    print("=" * 64)
    print("LIVING WORLD DIGEST (what's actually airing):")
    print(world.describe_world())
    print("-" * 64)

    out = Path(args.out)
    path = runner.run_once(seconds=args.seconds, out=out, world=world)
    print(f"\nBroadcast recorded -> {path} ({path.stat().st_size} bytes)")
    print(f"Verify: ffprobe \"{path}\"")
    print("-" * 64)
    print("MORNING REPORT:")
    rep = world.morning_report()
    print(f"  shows: {rep['stats']['shows']} | relationships: {rep['stats']['relationships']}")
    for e in rep["recent_events"]:
        print(f"  - {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())