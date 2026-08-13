#!/usr/bin/env python3
"""Curated SNES-style pixel-art cast + backgrounds + promo art.

HONESTY NOTE (substance-over-slop): these are PROCEDURAL, curated placeholder
sprites drawn on a proper SNES 15-bit palette -- NOT claims of ROM rips. The
authentic path (real ROMs under RetroArch -> capture) is the documented future
upgrade (see RESEARCH_SNES). Every asset passes deterministic content gates and
is catalogued with `method:"procedural_curated"`.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np

# --- SNES 15-bit colour table (5-bit channels, "bits 0-4 R, 5-9 G, 10-14 B") --
# Stored as 8-bit RGB produced from 15-bit values -> authentic SNES gamut.
def _s(r, g, b):
    return (r << 3, g << 3, b << 3)

PAL = {
    "transparent": (0, 0, 0, 0),
    "black":   _s(0, 0, 0),
    "white":   _s(31, 31, 31),
    "dk_gray": _s(16, 16, 16),
    "md_gray": _s(21, 21, 21),
    "red":     _s(27, 4, 4),
    "br_red":  _s(31, 8, 8),
    "blue":    _s(4, 8, 27),
    "dk_blue": _s(2, 5, 18),
    "lt_blue": _s(10, 20, 31),
    "green":   _s(4, 27, 8),
    "dk_green":_s(2, 16, 5),
    "lt_green":_s(12, 31, 12),
    "pink":    _s(31, 12, 24),
    "lt_pink": _s(31, 20, 26),
    "yellow":  _s(31, 27, 6),
    "gold":    _s(30, 24, 5),
    "lt_yellow":_s(31, 31, 14),
    "orange":  _s(31, 16, 4),
    "tan":     _s(27, 18, 12),
    "br_tan":  _s(19, 13, 9),
    "brown":   _s(17, 11, 6),
    "dk_brown":_s(11, 7, 4),
    "purple":  _s(19, 6, 27),
    "dk_purple":_s(13, 4, 19),
    "teal":    _s(6, 23, 23),
    "maroon":  _s(20, 4, 10),
}
TOK = {  # single-char tokens for authoring maps
    ".": "transparent", "K": "black", "W": "white", "g": "dk_gray", "G": "md_gray",
    "R": "red", "r": "br_red", "B": "blue", "b": "dk_blue", "L": "lt_blue",
    "Gg": "green", "D": "dk_green", "E": "lt_green", "P": "pink", "p": "lt_pink",
    "Y": "yellow", "y": "lt_yellow", "O": "orange", "T": "tan", "t": "br_tan",
    "N": "brown", "n": "dk_brown", "U": "purple", "u": "dk_purple", "C": "teal",
    "M": "maroon",
}
# mapping token -> palette key (2-char tokens must be handled with care; keep 1-char)
CH = { "K":"black","W":"white","g":"dk_gray","G":"md_gray","R":"red","r":"br_red",
       "B":"blue","b":"dk_blue","L":"lt_blue","D":"green","d":"dk_green","E":"lt_green",
       "P":"pink","p":"lt_pink","Y":"yellow","y":"lt_yellow","O":"orange","T":"tan",
       "t":"br_tan","N":"brown","n":"dk_brown","U":"purple","u":"dk_purple","C":"teal",
       "M":"maroon" }


def _rgb(name: str):
    c = PAL[name]
    return (c[0], c[1], c[2], 255)


class Canvas:
    """Small pixel canvas for authoring a sprite frame."""
    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.grid = np.full((h, w), -1, dtype=np.int8)  # -1 = transparent

    def px(self, x, y, name):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.grid[y, x] = list(PAL).index(name)

    def rect(self, x0, y0, x1, y1, name):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.px(x, y, name)

    def map(self, rows, y0=0, x0=0):
        """Draw an ASCII map (each char = token in CH, '.' = transparent)."""
        for dy, row in enumerate(rows):
            for dx, ch in enumerate(row):
                if ch == ".":
                    continue
                name = CH.get(ch)
                if name:
                    self.px(x0 + dx, y0 + dy, name)

    def blit(self, other: "Canvas", x0, y0):
        sy = max(0, -y0); sx = max(0, -x0)
        for y in range(sy, other.h):
            for x in range(sx, other.w):
                v = int(other.grid[y, x])
                if v >= 0:
                    self.px(x0 + x, y0 + y, list(PAL)[v])

    def image(self):
        from PIL import Image
        h, w = self.grid.shape
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        px = img.load()
        for y in range(h):
            for x in range(w):
                v = int(self.grid[y, x])
                if v >= 0:
                    px[x, y] = _rgb(list(PAL)[v])
        return img


# --- Character manifest: per-cast colour/accessory palette -------------------
# keys: cap/hair/shirt/overalls/shoes/skin + hat style + hair length
CAST = {
    "mario":  dict(cap="red",  hair="brown", shirt="red", overalls="blue",
                   shoes="brown", skin="tan", hat="cap", hair_len=0, extra="mario"),
    "luigi":  dict(cap="green", hair="brown", shirt="green", overalls="blue",
                   shoes="brown", skin="tan", hat="cap", hair_len=0, extra="mario"),
    "peach":  dict(cap="gold", hair="yellow", shirt="pink", overalls="pink",
                   shoes="red", skin="tan", hat="crown", hair_len=1, extra="princess"),
    "toad":   dict(cap="white", hair="tan", shirt="blue", overalls="white",
                   shoes="teal", skin="tan", hat="mushroom", hair_len=0, extra="toad"),
    "bowser": dict(cap="shell", hair="orange", shirt="green", overalls="dk_green",
                   shoes="brown", skin="green", hat="none", hair_len=1, extra="bowser"),
    "yoshi":  dict(cap="none", hair="none", shirt="green", overalls="lt_green",
                   shoes="green", skin="lt_green", hat="none", hair_len=0, extra="yoshi"),
    "wario":  dict(cap="yellow", hair="brown", shirt="purple", overalls="yellow",
                   shoes="brown", skin="tan", hat="cap", hair_len=0, extra="wario"),
    "link":   dict(cap="green", hair="yellow", shirt="green", overalls="tunic",
                   shoes="brown", skin="tan", hat="elfcap", hair_len=1, extra="link"),
    "zelda":  dict(cap="gold", hair="yellow", shirt="pink", overalls="purple",
                   shoes="red", skin="tan", hat="crown", hair_len=1, extra="princess"),
}


def _infer(spec, key, fallback=""):
    v = spec.get(key)
    return v if v in PAL else fallback


def paint_character(kind: str, pose: str = "idle") -> Canvas:
    """Paint one 16x20 animation frame for a cast member in a given pose."""
    spec = CAST.get(kind, CAST["mario"])
    c = Canvas(16, 20)
    skin = _infer(spec, "skin", "tan")
    shirt = _infer(spec, "shirt", "red")
    overalls = _infer(spec, "overalls", "blue")
    shoes = _infer(spec, "shoes", "brown")
    hat = _infer(spec, "cap", "red")
    hair = _infer(spec, "hair", "brown")
    ext = spec.get("extra")

    # ---------- HEAD (y0..7) ----------
    c.rect(4, 0, 11, 7, skin)          # face block
    # eyes
    c.px(6, 3, "black"); c.px(9, 3, "black")
    # mouth by pose (talk = open, happy = smile)
    if pose in ("talk_a", "talk_b"):
        c.px(7, 6, "black"); c.px(8, 6, "black")
    else:
        c.px(7, 6, "black"); c.px(8, 6, skin); c.px(8, 6, "brown")
    # hair/mouth styling per pose
    if pose == "happy":
        c.px(7, 5, "black"); c.px(8, 5, "black")

    # hat / hair / crown
    if ext == "mario":        # classic cap, brim, 'M'
        c.rect(4, 0, 11, 3, hat)
        c.px(5, 0, "black"); c.px(6, 0, "black")   # hair tufts
        c.px(7, 2, "black")  # brim
    elif ext == "princess":   # crown + long hair
        c.rect(5, 0, 10, 1, hat)
        c.px(6, 0, "black"); c.px(7, 0, "black"); c.px(8, 0, "black")
        c.rect(3, 1, 4, 2, hair); c.rect(11, 1, 12, 2, hair)
        c.rect(3, 3, 4, 6, hair); c.rect(11, 3, 12, 6, hair)
    elif ext == "mushroom":   # toad: white cap with red spots
        c.rect(3, 0, 12, 3, hat)
        c.px(5, 1, "red"); c.px(9, 1, "red"); c.px(7, 2, "red")
    elif ext == "bowser":     # spiky shell head
        c.rect(4, 0, 11, 2, "dk_green")
        c.px(3, 0, "orange"); c.px(12, 0, "orange")
        c.rect(4, 0, 5, 1, "green")
    elif ext == "elfcap":     # link pointed cap
        c.rect(4, 0, 11, 2, hat)
    elif ext == "wario":      # yellow cap w/ brim
        c.rect(4, 0, 11, 3, hat)
        c.px(5, 0, "black"); c.px(6, 0, "black")

    # ---------- TORSO (y8..14) ----------
    c.rect(5, 8, 10, 14, shirt)
    if ext in ("mario", "wario", "luigi"):
        # overall straps
        c.px(5, 9, overalls); c.px(10, 9, overalls)
        c.rect(5, 12, 10, 14, overalls)
        c.px(4, 12, overalls); c.px(11, 12, overalls)  # trouser sides
    elif ext == "princess":
        c.rect(5, 9, 10, 14, "pink")
        c.px(4, 13, "pink"); c.px(11, 13, "pink")
        c.px(5, 8, "gold"); c.px(6, 8, "gold")  # necklace
    elif ext == "toad":
        c.rect(6, 8, 9, 14, "white")       # vest
        c.px(7, 8, "red"); c.px(8, 8, "red")
    elif ext == "bowser":
        c.rect(4, 8, 11, 14, "dk_green")
        c.rect(5, 11, 10, 12, "yellow")    # belly scales
    elif ext == "yoshi":
        c.rect(4, 8, 11, 13, "lt_green")
        c.px(5, 14, "red"); c.px(6, 14, "red")   # saddle

    # ---------- ARMS (pose-dependent) ----------
    # down (idle / walk)
    c.px(4, 11, shirt); c.px(4, 12, shirt)
    c.px(11, 11, shirt); c.px(11, 12, shirt)
    if pose == "happy":
        c.px(3, 9, shirt); c.px(3, 10, shirt)    # arm(s) up
        c.px(12, 9, shirt); c.px(12, 10, shirt)
    elif pose in ("attack", "jump"):
        c.px(12, 8, "black"); c.px(3, 8, shirt)  # punch arm forward
    elif pose == "talk_a":
        c.px(3, 9, shirt)                        # one hand gesticulating
    # hands (skin)
    c.px(3, 13, skin); c.px(12, 13, skin)

    # ---------- LEGS (pose-dependent) ----------
    def stance(la, ra, lb, rb, lx, rx):
        c.px(lx, 15, overalls); c.px(lx, 16, overalls)
        c.px(rx, 15, overalls); c.px(rx, 16, overalls)
        c.px(lx, 15, la); c.px(lx, 16, lb)
        c.px(rx, 15, ra); c.px(rx, 16, rb)

    if pose in ("walk_a", "jump", "attack"):
        stance(overalls, overalls, overalls, overalls, 6, 9)
        c.px(6, 17, shoes); c.px(9, 17, shoes); c.px(6, 18, shoes)  # stride
    elif pose == "walk_b":
        stance(overalls, overalls, overalls, overalls, 6, 9)
        c.px(9, 17, shoes); c.px(9, 18, shoes)
    else:  # idle / talk / happy / think
        stance(overalls, overalls, overalls, overalls, 6, 9)
        c.px(6, 17, shoes); c.px(9, 17, shoes)
    return c


# Poses the painter produces; the animation library maps motion names -> these.
POSE_KEYS = ("idle", "talk_a", "talk_b", "walk_a", "walk_b", "happy", "jump", "attack")


class SpriteBank:
    """Builds & caches per-character pose frames. Movement library drives it."""

    def __init__(self, scale: int = 4):
        self.scale = scale
        self._cache: dict[tuple[str, str], "Canvas"] = {}

    def frame(self, kind: str, pose: str) -> "Canvas":
        key = (kind, pose)
        if key not in self._cache:
            pose = pose if pose in POSE_KEYS else "idle"
            self._cache[key] = paint_character(kind, pose)
        return self._cache[key]

    def image(self, kind: str, pose: str = "idle"):
        c = self.frame(kind, pose)
        img = c.image()
        if self.scale != 1:
            img = img.resize((c.w * self.scale, c.h * self.scale), 0)  # nearest
        return img

    def characters(self) -> list[str]:
        return list(CAST.keys())


