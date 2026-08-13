#!/usr/bin/env python3
"""Broadcast segment DSL -- the renderable unit.

Unlike the old broadcast_engine.py (dataclasses that emit *strings* nothing
consumes), a BroadcastSegment is a structured, renderable plan: cast on screen,
background, ordered dialogue beats (speaker+line+movement), ticker, lower-thirds,
rating, and whether it carries a commercial pod / promo / PSA / hand-off.

The renderer reads this structure directly. Gary (decision) fills it from world
state; the runner feeds the frames to ffmpeg.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Cast:
    name: str
    kind: str
    title: str = ""       # lower-third label
    motion: str = "idle"


@dataclass
class Beat:
    speaker: str
    text: str
    motion: str = "talk"
    frames: int = 90      # SNES typewriter pace


@dataclass
class BroadcastSegment:
    seg_id: str
    title: str
    fmt: str
    daypart: str = ""
    background: str = "studio"
    cast: list[Cast] = field(default_factory=list)
    beats: list[Beat] = field(default_factory=list)
    ticker: list[str] = field(default_factory=list)
    rating: str = "TV-PG"
    bumper: bool = True
    commercial: bool = False
    promo: bool = False
    psa: Optional[str] = None
    station_id: bool = False
    hand_off: str = ""

    def by_kind(self, kind: str) -> Optional[Cast]:
        for c in self.cast:
            if c.kind == kind:
                return c
        return None

    def dialogue_lines(self) -> list[Beat]:
        return self.beats


@dataclass
class OTAFrame:
    """A single frame command for the renderer (may carry a full element)."""
    element: str          # show | promo | commercial | psa | station_id | color_bars
    painter: object = None
    text: str = ""