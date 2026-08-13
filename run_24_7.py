#!/usr/bin/env python3
"""T3MPLATE TV WORLD -- the 24/7 broadcast loop.

Runs the network continuously:
  * default: records an append-only MP4 chunk per aired segment into
    OUTPUT/recordings/ and advances the world (24/7, Ctrl+C to stop).
  * --stream: pushes a live video feed to Twitch using the TWITCH_STREAM_KEY
    from .env (video-only in this MVP).

Each cycle: fixed 90s grid slot -> Gary decides from world-state -> renders
SNES dialogue + chrome with movement -> records/streams -> on_air() applies the
causal feedback that keeps continuity alive.
"""
from __future__ import annotations

import argparse
import sys

from tvn import runner
from tvn.config import SETTINGS


def main() -> int:
    ap = argparse.ArgumentParser(description="Run the T3MPLATE TV broadcast 24/7")
    ap.add_argument("--stream", action="store_true",
                    help="stream live to Twitch (needs TWITCH_STREAM_KEY in .env)")
    ap.add_argument("--seconds", type=float, default=12.0,
                    help="seconds per aired segment (record mode)")
    args = ap.parse_args()

    if args.stream and not SETTINGS.twitch_stream_key:
        print("No TWITCH_STREAM_KEY in .env -- cannot stream. Set it, or run record mode.")
        return 2

    runner.run_forever(stream=args.stream, seconds=args.seconds)
    return 0


if __name__ == "__main__":
    sys.exit(main())