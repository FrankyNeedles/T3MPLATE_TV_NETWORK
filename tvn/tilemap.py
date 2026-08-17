#!/usr/bin/env python3
"""T3MPLATE-constructed SNES genre sets -- built, not repurposed.

Improvement 2 (asset-auth gap): the MVP's 8 "genre-specific" backgrounds were
5 SMW emulator screenshots relabeled (news_studio==city==sports_arena, etc.).
This module CONSTRUCTS 8 genuinely-distinct 256x224 backgrounds using the SNES
15-bit palette (tvn.sprites.PAL / _s) and tile-pattern layout logic inspired by
the dead .bin tilemap index maps in assets/backgrounds/ (which are real SNES
map16 16-bit words: tile# | hflip | vflip | palette | priority).

The .bin files carry no tile pixel graphics (no tileset sheets exist), so we
compose the sets from SNES-15bit-colored rects following SMW tilemap LAYOUTS --
each genre gets a unique composition. Full ROM-tile pixel extraction is the
documented follow-on (RESEARCH_SNES); this is the honest in-repo step that
stops the broadcast from showing Nintendo's cave levels as "news studios".

Public API:
    decode_tilemap_file(path) -> list[int]   # read a .bin -> 16-bit words
    is_test_pattern(words) -> bool            # 0xC10C-repeat detector
    constructed_set(set_name) -> Image        # 8 distinct SNES-15bit sets
    TILEMAP_SETS                               # the 8 genre set names
"""
from __future__ import annotations

import struct
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image, ImageDraw

from .sprites import PAL, _s, Canvas
from .config import SETTINGS
from . import assets

NATIVE = SETTINGS.res_native  # (256, 224)

# The 8 genre set names used by programming.DAYPART_FORMATS + content.SHOW_PRESETS.
TILEMAP_SETS = ("news_studio", "talk_show", "diner", "cartoon_house",
                "city", "sports_arena", "studio", "game_show")


# --- .bin tilemap decoding (SNES map16 16-bit word format) ---------------
# Per RESEARCH_SNES.md: a VRAM tilemap word is:
#   bits 0-9   = tile number
#   bit  10    = hflip
#   bit  11    = vflip
#   bits 12-13 = palette index
#   bit  14    = priority (0=under,1=over)
def decode_tilemap_file(path: Path | str) -> list[int]:
    """Read a raw .bin tilemap file -> list of 16-bit little-endian words."""
    data = Path(path).read_bytes()
    if len(data) % 2 != 0:
        data = data[:-1]  # trim any trailing odd byte
    return list(struct.unpack("<%dH" % (len(data) // 2), data))


def tilemap_word(tile: int, hflip: bool = False, vflip: bool = False,
                 palette: int = 0, priority: int = 0) -> int:
    """Assemble a 16-bit SNES map16 tilemap word from components."""
    return (tile & 0x3FF) | (int(hflip) << 10) | (int(vflip) << 11) \
           | ((palette & 0x7) << 12) | (int(priority) << 14)


def is_test_pattern(words: list[int]) -> bool:
    """True if the tilemap is a degenerate test pattern.

    Catches two failure modes documented in RESEARCH_SNES.md:
      (1) a pure-repeat fill (all 0xC10C) -- distinct < 8; or
      (2) a low-cardinality repeating pattern (battle_contra_0x80000.bin: tile
      127 alone appears 157/2048 = 7.7% of cells, the other 516 "distinct" words
      are mostly SMW empty-space markers 0x0001/0xFFFE/0xFFFF. A real SMW level
      has no single tile dominating >5% of the map). Flag a tile appearing in
      >5% of cells as a test-pattern fill.
    """
    if not words:
        return True
    if len(set(words)) < 8:
        return True  # pure-repeat fill
    from collections import Counter
    most_common_count = Counter(words).most_common(1)[0][1]
    return most_common_count / len(words) > 0.05


def tile_grid(words: list[int], cols: int = 32) -> np.ndarray:
    """Reshape a flat tilemap word list into a (rows, cols) grid of tile indices."""
    n = len(words)
    rows = n // max(1, cols)
    return np.array(words[:rows * cols]).reshape(rows, cols)


# --- 8 distinct genre sets, composed from SNES-15bit palette rects -------
# Each builder produces a 256x224 image using only PAL colors (channels div-by-8).
# The .bin tilemap layouts (grids) inspire the composition, but pixels are
# authored here as SNES-15bit rectangles so the output is genuinely ours, not a
# repurposed Nintendo screenshot.

def _canvas() -> Canvas:
    return Canvas(NATIVE[0], NATIVE[1])


def _set_news_studio() -> Image.Image:
    """News studio: cyclorama sky, multi-panel desk, lower-third zone."""
    c = _canvas()
    c.rect(0, 0, 255, 111, "lt_blue")            # cyclorama (SNES sky gradient band)
    c.rect(0, 112, 255, 159, "dk_blue")           # desk band
    c.rect(0, 160, 255, 223, "blue")              # floor
    # desk consoles: 3 distinct panels
    c.rect(30, 120, 80, 150, "md_gray")
    c.rect(100, 120, 150, 150, "md_gray")
    c.rect(190, 120, 230, 150, "md_gray")
    c.rect(30, 150, 80, 158, "dk_gray")
    # backdrop marquee panel
    c.rect(48, 24, 200, 96, "maroon")
    return c.image()


def _set_talk_show() -> Image.Image:
    """Talk show: purple suite, sofa backdrop, stage floor."""
    c = _canvas()
    c.rect(0, 0, 255, 129, "purple")
    c.rect(0, 130, 255, 223, "dk_purple")
    c.rect(20, 30, 236, 128, "maroon")            # sofa backdrop
    c.rect(30, 150, 226, 168, "tan")              # stage
    c.rect(80, 132, 176, 156, "dk_gray")          # couch
    # side table + lamp
    c.rect(40, 140, 56, 156, "dk_gray")
    c.rect(48, 132, 56, 140, "yellow")
    return c.image()


def _set_diner() -> Image.Image:
    """Diner: tan booth seating, counter, window."""
    c = _canvas()
    c.rect(0, 0, 255, 99, "tan")                  # ceiling
    c.rect(0, 100, 255, 223, "brown")             # booth floor
    c.rect(30, 50, 110, 90, "white")              # window
    c.rect(40, 60, 100, 88, "lt_blue")            # window view
    c.rect(120, 70, 250, 160, "maroon")           # counter
    c.rect(60, 110, 100, 150, "dk_gray")          # booth table
    return c.image()


def _set_cartoon_house() -> Image.Image:
    """Cartoon house: bright sky, playhouse, door."""
    c = _canvas()
    c.rect(0, 0, 255, 159, "lt_blue")             # sky
    c.rect(0, 160, 255, 223, "green")             # grass
    c.rect(90, 70, 190, 158, "orange")            # playhouse body
    c.rect(120, 110, 160, 150, "dk_gray")         # door
    c.rect(96, 74, 130, 96, "dk_blue")            # window
    return c.image()


def _set_city() -> Image.Image:
    """City: night skyline with window grid (distinct from diner/cartoon)."""
    c = _canvas()
    c.rect(0, 0, 255, 159, "dk_blue")             # night sky
    c.rect(0, 160, 255, 223, "black")             # street
    # skyline: 7 distinct buildings
    for x in (20, 56, 92, 128, 164, 200, 236):
        bh = c.rect(x, 110, x + 18, 158, "blue")
        c.rect(x + 4, 90, x + 14, 109, "blue")    # window per building top
    # lit windows (yellow) on alternate buildings
    for x in (30, 128, 200):
        c.rect(x, 96, x + 8, 104, "yellow")
    return c.image()


def _set_sports_arena() -> Image.Image:
    """Sports arena: stadium field + stands (distinct from city)."""
    c = _canvas()
    c.rect(0, 0, 255, 119, "black")               # night stands (dark)
    c.rect(0, 120, 255, 223, "green")             # field/turf
    c.rect(0, 120, 255, 134, "yellow")            # mid-field line
    c.rect(40, 40, 216, 118, "dk_blue")            # stands
    # stadium light posts
    c.rect(40, 30, 44, 40, "yellow")
    c.rect(212, 30, 216, 40, "yellow")
    return c.image()


def _set_studio() -> Image.Image:
    """Network studio: branded marquee + cyclorama (distinct from talk_show)."""
    c = _canvas()
    c.rect(0, 0, 255, 159, "dk_blue")             # cyclorama back
    c.rect(0, 160, 255, 223, "blue")              # floor
    c.rect(48, 24, 200, 96, "dk_gray")             # branded marquee block
    c.rect(60, 40, 184, 80, "dk_purple")           # marquee face
    c.rect(0, 120, 255, 128, "lt_blue")            # desk/front
    return c.image()


def _set_game_show() -> Image.Image:
    """Game show: bright set + contestant podiums (distinct from all above)."""
    c = _canvas()
    c.rect(0, 0, 255, 119, "lt_blue")             # sky ceiling
    c.rect(0, 120, 255, 223, "dk_blue")           # floor
    c.rect(30, 120, 60, 158, "red")               # podium 1
    c.rect(98, 120, 128, 158, "red")              # podium 2
    c.rect(166, 120, 196, 158, "red")             # podium 3
    c.rect(48, 40, 200, 100, "yellow")            # big buzzer backdrop
    return c.image()


_BUILDERS = {
    "news_studio": _set_news_studio,
    "talk_show": _set_talk_show,
    "diner": _set_diner,
    "cartoon_house": _set_cartoon_house,
    "city": _set_city,
    "sports_arena": _set_sports_arena,
    "studio": _set_studio,
    "game_show": _set_game_show,
}


def constructed_set(set_name: str) -> Image.Image:
    """Build a SNES-15bit-constructed genre set for `set_name`.

    Returns a 256x224 RGBA image using ONLY SNES 15-bit palette colors. Falls
    back to a generic studio if the name is unknown.
    """
    builder = _BUILDERS.get(set_name, _set_studio)
    return builder()


def ensure_constructed_sets() -> dict[str, str]:
    """Materialize the 8 constructed sets to assets/backgrounds/ as
    t3mplt_<set>.png and return {set_name: file_path}. Idempotent."""
    out_dir = SETTINGS.root / "assets" / "backgrounds"
    written: dict[str, str] = {}
    for name in TILEMAP_SETS:
        path = out_dir / f"t3mplt_{name}.png"
        written[name] = str(path)
        if path.exists() and path.stat().st_size > 0:
            continue
        img = constructed_set(name)
        img.save(str(path))
    return written
