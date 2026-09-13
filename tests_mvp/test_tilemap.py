"""Tests for Improvement 2 -- T3MPLATE-constructed genre sets from .bin tilemaps.

The 6 .bin files in assets/backgrounds/ are SNES map16 index maps (no tileset
graphics). tvn.tilemap decodes them and CONSTRUCTS 8 genuinely-distinct genre
backgrounds using the SNES 15-bit palette (tvn.sprites._s / PAL) -- no two sets
share pixels, no SMW screenshot reuse.

See research_findings_visual.md sections 3.2 (5 unique SMW screens for 8 labels)
and 5.6 (dead .bin files not referenced by code).
"""
import hashlib

import numpy as np
import pytest

from tvn import assets, tilemap
from tvn.config import SETTINGS


# ---- .bin decoding ------------------------------------------------------
def test_decode_tilemap_words():
    """Decode a .bin into 16-bit SNES tilemap words (tile | hflip | vflip | pal | pri)."""
    data = tilemap.decode_tilemap_file(SETTINGS.root / "assets" / "backgrounds"
                                       / "desert_zelda_0x90000.bin")
    assert len(data) == 2048  # 4096 bytes / 2
    # each word is a 16-bit int: bits 0-9 = tile#, 10 = hflip, 11 = vflip,
    # 12-13 = palette, 14 = priority (per RESEARCH_SNES.md)
    w = data[0]
    assert 0 <= w <= 0xFFFF


def test_battle_contra_is_test_pattern():
    """battle_contra_0x80000.bin is a pure repeating test pattern (0xC10C) --
    tilemap module must flag/skip it, not treat as a real level layout."""
    words = tilemap.decode_tilemap_file(SETTINGS.root / "assets" / "backgrounds"
                                       / "battle_contra_0x80000.bin")
    assert tilemap.is_test_pattern(words)


# ---- constructed genre sets --------------------------------------------
@pytest.mark.parametrize("set_name", [
    "news_studio", "talk_show", "diner", "cartoon_house",
    "city", "sports_arena", "studio", "game_show",
])
def test_eight_sets_constructed_distinct(set_name):
    """Each constructed T3MPLATE set must exist, pass the gate, and be
    pixel-distinct from every other constructed set."""
    img = tilemap.constructed_set(set_name)
    assert img.size == (256, 224)
    g = assets.gate_image(img, kind="background")
    assert g["all_passed"] is True
    assert g["checks"]["snes_palette_validity"] is True  # SNES 15-bit only


def test_constructed_sets_are_pairwise_distinct():
    """No two of the 8 constructed sets are pixel-identical (the SMW dup bug)."""
    sets = ["news_studio", "talk_show", "diner", "cartoon_house",
            "city", "sports_arena", "studio", "game_show"]
    hashes = {}
    for s in sets:
        img = tilemap.constructed_set(s)
        hashes[s] = hashlib.sha256(img.convert("RGBA").tobytes()).hexdigest()
    # all 8 must be unique
    assert len(set(hashes.values())) == 8, f"duplicate sets: {hashes}"


def test_construct_sets_use_only_snes_15bit_palette():
    """Every non-transparent pixel in a constructed set must be SNES 15-bit."""
    img = tilemap.constructed_set("city")
    arr = np.array(img.convert("RGB"))
    opaque = arr.reshape(-1, 3)
    nonblack = opaque[np.any(opaque != 0, axis=1)]
    for chan in nonblack.ravel():
        assert chan % 8 == 0, f"non-SNES color channel={chan}"
