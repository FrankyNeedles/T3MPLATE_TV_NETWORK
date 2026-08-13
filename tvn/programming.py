#!/usr/bin/env python3
"""Programming engine -- the fixed 90s daily grid.

Per RESEARCH_90S the original failure was a *loose daypart->random show* model.
Real 90s TV is predictable: same show at 6pm, prime 8-11, late news at 11. This
module locks the broadcast to a real daily grid so a viewer can guess the clock
from what's on screen, and models the commercial pod grammar + hand-offs.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time as dt_time
from typing import Optional

from . import content


@dataclass(frozen=True)
class Slot:
    start_min: int          # minutes since midnight (ET)
    daypart: str
    title: str
    fmt: str
    dur_min: int


# --- The fixed 24h grid (RESEARCH_90S sec 5, broad-brush for the MVP) --------
M = 60
GRID = [
    Slot(0 * M + 0, "late_night", "Late Night with Wario", "late_night", 35),
    Slot(0 * M + 35, "late_night", "Night Owls with Yoshi", "talk", 25),
    Slot(1 * M + 0, "overnight", "PSA Hour", "psa", 60),
    Slot(2 * M + 0, "overnight", "EarthBound: The Broadcast", "rerun", 60),
    Slot(3 * M + 0, "overnight", "The Power-Up 9000 Infomercial", "infomercial", 60),
    Slot(4 * M + 0, "overnight", "Mushroom Fade Mastery", "infomercial", 30),
    Slot(4 * M + 30, "overnight", "Infomercial + Test Pattern", "infomercial", 30),
    Slot(5 * M + 0, "overnight", "Zelda: Adventures in Hyrule (r)", "rerun", 60),
    Slot(6 * M + 0, "early_news", "T3TV Morning Update", "news", 30),
    Slot(6 * M + 30, "early_morning", "Farm & Home Report", "infomercial", 30),
    Slot(7 * M + 0, "morning", "Mushroom Morning", "morning", 120),
    Slot(9 * M + 0, "daytime", "Super Playhouse", "cartoon", 60),
    Slot(10 * M + 0, "daytime", "Name That Mushroom", "game_show", 60),
    Slot(11 * M + 0, "daytime", "Koopa & Chill", "talk", 60),
    Slot(12 * M + 0, "daytime", "Midday News", "news", 30),
    Slot(12 * M + 30, "daytime", "The Rings of Hyrule", "soap", 90),
    Slot(14 * M + 0, "daytime", "Bowser's Bitter Heir", "soap", 60),
    Slot(15 * M + 0, "daytime", "The Peach Report", "talk", 90),
    Slot(16 * M + 30, "early_fringe", "Luigi & Company (r)", "sitcom", 90),
    Slot(18 * M + 0, "early_news", "Eyewitness News at 6", "news", 30),
    Slot(18 * M + 30, "early_news", "Eyewitness News at 6:30", "news", 30),
    Slot(19 * M + 0, "access", "The Coin Block", "game_show", 30),
    Slot(19 * M + 30, "access", "Final Fantasy Facts", "game_show", 30),
    Slot(20 * M + 0, "prime", "The Super Mario Bros. Show", "sitcom", 60),
    Slot(21 * M + 0, "prime", "Chrono: A Link to the Present", "action", 120),
    Slot(23 * M + 0, "late_news", "News at 11", "news", 35),
    Slot(23 * M + 35, "late_night", "The Late Show with Wario", "late_night", 25),
]
GRID.sort(key=lambda s: s.start_min)


def get_current_daypart(now: Optional[datetime] = None) -> str:
    """Return the industry-style daypart block for a wall clock (RESEARCH_90S sec 1)."""
    now = now or datetime.now()
    t = now.time()
    if dt_time(23, 35) <= t or t < dt_time(1, 0):
        return "late_night"
    if dt_time(1, 0) <= t < dt_time(6, 0):
        return "overnight"
    if dt_time(6, 0) <= t < dt_time(7, 0):
        return "early_news"
    if dt_time(7, 0) <= t < dt_time(9, 0):
        return "morning"
    if dt_time(9, 0) <= t < dt_time(16, 30):
        return "daytime"
    if dt_time(16, 30) <= t < dt_time(18, 0):
        return "early_fringe"
    if dt_time(18, 0) <= t < dt_time(19, 0):
        return "early_news"
    if dt_time(19, 0) <= t < dt_time(20, 0):
        return "access"
    if dt_time(20, 0) <= t < dt_time(23, 0):
        return "prime"
    return "late_news"


def get_slot(now: Optional[datetime] = None) -> Slot:
    """Active grid slot for a given clock (mod-24h)."""
    now = now or datetime.now()
    minutes = now.hour * 60 + now.minute
    current = GRID[-1]
    for s in GRID:
        if s.start_min <= minutes:
            current = s
        else:
            break
    return current


def next_slot(current: Slot) -> Slot:
    idx = next((i for i, s in enumerate(GRID) if s.start_min == current.start_min),
               GRID.index(current))
    return GRID[(idx + 1) % len(GRID)]


# --- Commercial pod grammar (RESEARCH_90S sec 2) ------------------------------
@dataclass
class PodElement:
    kind: str            # promo | national | local | psa | station_id
    text: str
    seconds: int = 30


def build_pod(daypart: str, next_show: str = "", seed: Optional[int] = None) -> list[PodElement]:
    """A commercial pod is an ORDERED sequence: promo -> national xN ->
    local x1-2 -> station id. News/access skew local; prime skews national."""
    import random
    rng = random.Random(seed)
    local_pool = list(content.LOCAL_SPOTS)
    sport = next_show or "the next program"
    elements: list[PodElement] = []

    heavy_local = daypart in ("early_news", "early_morning", "access", "late_news")
    heavy_national = daypart in ("prime", "late_night")

    # 1. promo for the upcoming show
    elements.append(PodElement("promo", f"Next up: {sport}", 15))
    # 2. national spots (2-4)
    nationals = rng.sample(content.NATIONAL_SPOTS, k=rng.randint(2, 4))
    for n in nationals:
        elements.append(PodElement("national", n, 30))
    # 3. local spots (1-2; heavier when local)
    locals = rng.sample(local_pool, k=rng.randint(2, 3) if heavy_local else 1)
    for lo in locals:
        elements.append(PodElement("local", lo, 30))
    # 4. PSA in dayparts that cluster them (access/late)
    if daypart in ("access", "late_night", "overnight", "early_morning"):
        topic, agency = rng.choice(content.PSA_TOPICS)
        elements.append(PodElement("psa", f"{topic} - {agency}", 15))
    # 5. station id
    elements.append(PodElement("station_id", "T3TV - The Mushroom Network", 5))
    return elements


@dataclass
class HandOff:
    """The connective tissue between programs (RESEARCH_90S sec 2.6)."""
    from_show: str
    to_show: str
    next_tease: str
    tag: str = ""
    station_id: str = "T3TV - The Mushroom Network"


def build_handoff(from_show: str, to_show: str) -> HandOff:
    return HandOff(from_show=from_show, to_show=to_show,
                   next_tease=f"{to_show} is NEXT!",
                   tag=f"That's {from_show} for today. We'll see you at the top of the hour.")


def display_time(now: Optional[datetime] = None) -> str:
    now = now or datetime.now()
    return now.strftime("%I:%M %p").lstrip("0")