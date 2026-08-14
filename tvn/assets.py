#!/usr/bin/env python3
"""Asset kit: SNES set backgrounds + full-screen promo/commercial art + gates.

Draws on the same SNES palette as the cast. All art is *procedural curated*
placeholders (honest provenance in the catalog). The broadcast renderer reads
assets only through this module; every asset passes the RESEARCH_ASSETS content
gates (dimensions, alpha coverage, used-colour count, bbox ratio) before it may
reach a frame -- fail loud, quarantine, never slop.
"""
from __future__ import annotations

import json
import hashlib
from typing import Any
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .sprites import PAL, Canvas, _rgb, SpriteBank
from .config import SETTINGS

NATIVE = SETTINGS.res_native  # (256, 224)

# -- Deterministic noise-battery gates (RESEARCH_ASSETS 4.1/4.2) ---------------
def gate_image(img: Image.Image, n_tiles: int = 8, kind: str = "sprite",
               real_art: bool = False) -> dict[str, Any]:
    """Run content checks on an image. Returns metrics + all_passed bool.
    kind='background' relaxes the alpha/bbox bounds (full-frame sets are valid).
    real_art=True allows authentic SNES colors >15 (captured/curated frames)."""
    rgba = np.array(img.convert("RGBA"))
    alpha = rgba[..., 3]
    h, w = alpha.shape
    total = w * h
    opaque = int((alpha > 0).sum())
    coverage = opaque / total if total else 0.0

    # bounding box of non-transparent pixels
    idx = np.argwhere(alpha > 0)
    if idx.size == 0:
        bbox_ratio = 0.0
    else:
        (ymin, xmin), (ymax, xmax) = idx.min(0), idx.max(0)
        bbox_area = (ymax - ymin + 1) * (xmax - xmin + 1)
        bbox_ratio = bbox_area / total

    # used distinct opaque colours
    opaque_px = rgba[alpha > 0][:, :3]
    used_colors = len(np.unique(opaque_px, axis=0)) if len(opaque_px) else 0

    checks = {
        "alpha_coverage": round(coverage, 3),
        "bbox_ratio": round(bbox_ratio, 3),
        "used_colors": int(used_colors),
    }
    if kind == "background":
        ok = coverage > 0.5 and used_colors >= 2 and w >= 64 and h >= 64
    else:
        # Real SMW art legitimately uses more than 15 colors (native CGRAM
        # palettes + anti-aliased rips); the old upper bound was written for
        # procedural placeholder sprites. `real_art` keeps the anti-noise
        # floor (coverage, min colors, dims) but drops the cap and the bbox
        # bound that would wrongly quarantine authentic cropped frames (a
        # trimmed-to-content rip has bbox_ratio==1.0 by construction).
        hi = 400 if real_art else 15
        bbox_ok = (0.01 <= bbox_ratio <= 0.90) if not real_art else True
        # real dense sprites (e.g. SMW Yoshi) legitimately fill ~98% of their
        # trimmed box; only enforce the "not blank" floor (coverage>0.02) and
        # the sparse cap for procedural placeholders.
        cov_ok = (0.02 <= coverage <= 0.95) if not real_art else (coverage >= 0.02)
        ok = (
            cov_ok
            and bbox_ok
            and 2 <= used_colors <= hi
            and w >= 8 and h >= 8
        )
    return {"checks": checks, "all_passed": bool(ok), "width": w, "height": h, "kind": kind}


# -- Set backgrounds ----------------------------------------------------------
def _bg_canvas() -> Canvas:
    return Canvas(NATIVE[0], NATIVE[1])


def background(set_name: str) -> Image.Image:
    """Build a full-screen SNES set background (256x224).

    Prefers a real emulator-captured frame at assets/backgrounds/real_<set>.png
    (method:"emulator_capture", verified through gate_image); otherwise falls
    back to the procedural curated painter. The real capture must be a
    non-blank game screen -- anything failing the gate is quarantined here and
    the procedural painter is used (graceful, honest degradation).
    """
    real = _real_background(set_name)
    if real is not None:
        return real
    return _procedural_background(set_name)


_REAL_BG_CACHE: dict[str, Any] = {}
def _real_background(set_name: str) -> Any:
    """Load a staged real captured background for `set_name`, gated. None if
    absent or it fails the noise battery (=> caller uses procedural fallback)."""
    if set_name in _REAL_BG_CACHE:
        return _REAL_BG_CACHE[set_name]
    path = SETTINGS.root / "assets" / "backgrounds" / f"real_{set_name}.png"
    result = None
    if path.exists():
        img = Image.open(str(path)).convert("RGBA")
        if img.size != NATIVE:
            img = img.resize(NATIVE, Image.LANCZOS)
        g = gate_image(img, kind="background")
        if g["all_passed"]:
            result = img
        # else: quarantined (blank/noise) -> fall back to procedural painter
    _REAL_BG_CACHE[set_name] = result
    return result


def _procedural_background(set_name: str) -> Image.Image:
    """The original curated procedural set painter (fallback path)."""
    c = _bg_canvas()
    sky = "lt_blue"
    floor = "brown"
    mid = "blue"
    if set_name == "news_studio":
        c.rect(0, 0, 255, 119, "lt_blue")         # cyclorama
        c.rect(0, 120, 255, 159, "blue")          # desk band
        c.rect(0, 160, 255, 223, "dk_blue")       # floor
        c.rect(24, 16, 88, 76, "blue")            # backdrop panel
        c.rect(168, 16, 232, 76, "blue")
        c.rect(96, 96, 160, 118, "md_gray")       # anchor desk
        c.rect(0, 120, 255, 124, "white")         # desk edge
    elif set_name in ("talk_show", "studio", "game_show"):
        c.rect(0, 0, 255, 129, "purple")
        c.rect(0, 130, 255, 223, "dk_purple")
        c.rect(20, 30, 236, 128, "maroon")        # sofa backdrop
        c.rect(30, 150, 226, 168, "tan")          # stage
        c.rect(40, 40, 90, 74, "yellow"); c.rect(166, 40, 216, 74, "yellow")
    elif set_name == "diner":
        c.rect(0, 0, 255, 99, "tan")
        c.rect(0, 100, 255, 223, "brown")
        c.rect(30, 50, 110, 90, "white")          # window
        c.rect(40, 60, 100, 88, "lt_blue")
        c.rect(120, 70, 250, 160, "maroon")       # counter
    elif set_name == "cartoon_house":
        c.rect(0, 0, 255, 159, "lt_blue")
        c.rect(0, 160, 255, 223, "green")
        c.rect(60, 70, 200, 158, "orange")        # house
        c.rect(96, 108, 164, 158, "brown")        # door
    elif set_name == "city":
        c.rect(0, 0, 255, 159, "dk_blue")
        c.rect(0, 160, 255, 223, "black")
        for x in (20, 56, 92, 128, 164, 200, 236):
            c.rect(x, 110, x + 18, 158, "blue")
            c.rect(x + 4, 90, x + 14, 109, "blue")
    elif set_name == "sports_arena":
        c.rect(0, 0, 255, 119, "black")
        c.rect(0, 120, 255, 223, "yellow")
        c.rect(0, 120, 255, 134, "white")
        c.rect(40, 40, 216, 118, "blue")
    elif set_name == "batcave":
        c.rect(0, 0, 255, 223, "black")
        c.rect(20, 20, 70, 70, "dk_gray")
        c.rect(30, 90, 90, 150, "dk_gray")
        c.rect(190, 30, 240, 110, "dk_gray")
        c.rect(20, 120, 120, 170, "dk_gray")
    else:  # generic studio
        c.rect(0, 0, 255, 159, "blue")
        c.rect(0, 160, 255, 223, "dk_blue")
    return c.image()


# -- SNES full-screen promo / commercial art ---------------------------------
_FONT_CACHE: dict[int, Any] = {}
def _big_font(size: int):
    if size not in _FONT_CACHE:
        try:
            _FONT_CACHE[size] = ImageFont.truetype("arialbd.ttf", size)
        except Exception:
            _FONT_CACHE[size] = ImageFont.load_default()
    return _FONT_CACHE[size]


def promo_card(kind: str, title: str, subtitle: str = "", brand: str = "T3TV") -> Image.Image:
    """Full-screen 90s/SNES promo or ad card (the SNES title-screen look)."""
    img = Image.new("RGBA", NATIVE, (10, 10, 20, 255))
    d = ImageDraw.Draw(img)
    # chunky diagonal band (chrome gradient) -- authentic 90s CG feel
    for i in range(NATIVE[1]):
        shade = 24 + int(10 * abs((i / NATIVE[1]) - 0.5) * 4)
        band = shade if i < 150 else shade - 8
        d.line([(0, i), (NATIVE[0], i)], fill=(band, band, band + 6, 255))
    # accent colour per kind
    accent = {"national": (0, 120, 255), "local": (200, 40, 40),
              "promo": (255, 180, 0), "psa": (0, 150, 90)}.get(kind, (120, 120, 200))
    if kind == "national":   # giant hero block (SNES box-art vibe)
        d.rectangle([16, 40, 240, 150], outline=accent + (255,), width=3)
        d.rectangle([22, 46, 234, 144], fill=(20, 20, 40, 255))
        d.ellipse([110, 70, 146, 106], fill=accent + (255,))       # glossy sphere
    elif kind == "psa":      # centred shield
        d.polygon([(128, 30), (200, 80), (180, 190), (76, 190), (56, 80)],
                  outline=(255, 255, 255, 255), fill=(40, 40, 70, 255))
    else:                    # local / promo banner
        d.rectangle([0, 90, 255, 160], fill=accent + (255,))
        d.line([(0, 90), (255, 90)], fill=(255, 255, 255, 255), width=2)
        d.line([(0, 160), (255, 160)], fill=(0, 0, 0, 255), width=3)
    # text
    title = title.upper()[:14]
    oy = 160 if kind in ("local", "promo") else 168
    _text_center(d, title, NATIVE[0] // 2, oy, _big_font(20), (255, 255, 255), outline=(0, 0, 0))
    if subtitle:
        _text_center(d, subtitle.upper()[:30], NATIVE[0] // 2, oy + 22, _big_font(10),
                     (255, 255, 200))
    _text_center(d, brand, 12 if kind != "psa" else 128, 210, _big_font(8), (210, 210, 210))
    return img


def _text_center(d, text, x, y, font, fill, outline=None):
    bbox = d.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    if outline:
        d.text((x - w / 2, y), text, font=font, fill=outline,
               stroke_width=2, stroke_fill=(0, 0, 0))
    d.text((x - w / 2, y), text, font=font, fill=fill)


# -- Catalog (honest, append-only) --------------------------------------------
def _load_manifest(p: Path) -> list[dict]:
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return [data]
            if isinstance(data, list):
                return data
        except Exception:
            pass
    return []


def build_catalog() -> Path:
    """Write assets/catalog.json with honest provenance + gate results.

    Real captured/curated assets carry `method:"emulator_capture"`/`"curated_rip"`
    with {game, rom_sha256 | source_url, palette_source, frames}; procedural
    placeholders keep `method:"procedural_curated"`. Nothing real is labelled
    procedural_curated.
    """
    def sha(img: Image.Image) -> str:
        return hashlib.sha256(img.tobytes()).hexdigest()[:16]

    bg_entries = []
    # 1) real emulator-captured backgrounds (from assets/backgrounds/manifest.json)
    for m in _load_manifest(SETTINGS.root/"assets"/"backgrounds"/"manifest.json"):
        f = SETTINGS.root/"assets"/"backgrounds"/m["file"]
        img = Image.open(str(f)).convert("RGBA")
        gate = gate_image(img, kind="background")
        bg_entries.append({
            "asset_id": m["asset_id"], "asset_type": "background",
            "status": "ready" if gate["all_passed"] else "quarantined",
            "provenance": {
                "method": "emulator_capture", "game": m["game"],
                "rom_sha256": m["rom_sha256"], "emulator": m["emulator"],
                "palette_source": "native SNES rendered output",
            },
            "artifact": {"dimensions": img.size, "sha256": sha(img)},
            "verification": {"noise_battery": gate},
        })
    # 2) procedural placeholders for sets that have NO real capture (fallback)
    real_sets = {m["set_name"] for m in _load_manifest(
        SETTINGS.root/"assets"/"backgrounds"/"manifest.json")}
    for name in ("news_studio", "talk_show", "diner", "cartoon_house",
                 "city", "sports_arena", "batcave", "studio", "game_show"):
        if name in real_sets:
            continue
        img = background(name)
        gate = gate_image(img, kind="background")
        bg_entries.append({
            "asset_id": f"bg_{name}", "asset_type": "background",
            "status": "ready" if gate["all_passed"] else "quarantined",
            "provenance": {"method": "procedural_curated", "note": "fallback; not a ROM rip"},
            "artifact": {"dimensions": img.size, "sha256": sha(img)},
            "verification": {"noise_battery": gate},
        })

    # sprites
    bank = SpriteBank(1)
    spr_entries = []
    # real curated movements (from assets/movements/<char>/manifest.json)
    mov_dir = SETTINGS.root / "assets" / "movements"
    if mov_dir.exists():
        for cdir in sorted(mov_dir.iterdir()):
            if not cdir.is_dir():
                continue
            mm = _load_manifest(cdir / "manifest.json")
            if not mm:
                continue
            mm = mm[0]
            for cell in _load_manifest(cdir / "cells.json"):
                f = cdir / cell["file"]
                img = Image.open(str(f)).convert("RGBA")
                gate = gate_image(img, real_art=True)
                spr_entries.append({
                    "asset_id": f"spr_{mm['character']}_{cell['pose']}",
                    "asset_type": "sprite",
                    "status": "ready" if gate["all_passed"] else "quarantined",
                    "provenance": {
                        "method": "curated_rip", "game": mm["game"],
                        "rom_sha256": mm["rom_sha256"], "source_url": mm["source_url"],
                        "palette_source": mm["palette_source"],
                    },
                    "artifact": {"dimensions": img.size, "sha256": sha(img)},
                    "verification": {"noise_battery": gate},
                })
    # procedural sprites (fallback) for cast without an uploaded real frame
    real_poses = set()
    for e in spr_entries:
        real_poses.add(e["asset_id"].replace("spr_", "").rsplit("_", 1)[0])
    for kind in bank.characters():
        if kind in real_poses:
            continue
        img = bank.image(kind, "idle")
        gate = gate_image(img)
        spr_entries.append({
            "asset_id": f"spr_{kind}", "asset_type": "sprite",
            "status": "ready" if gate["all_passed"] else "quarantined",
            "provenance": {"method": "procedural_curated", "note": "fallback; not a ROM rip"},
            "artifact": {"dimensions": img.size, "sha256": sha(img)},
            "verification": {"noise_battery": gate},
        })

    # audio provenance (real emulator-captured beds)
    audio_entries = []
    for m in _load_manifest(SETTINGS.root/"assets"/"audio"/"manifest.json"):
        f = SETTINGS.root/"assets"/"audio"/m["file"]
        audio_entries.append({
            "asset_id": m["asset_id"], "asset_type": "audio",
            "status": "ready" if m.get("non_silent") else "quarantined",
            "provenance": {
                "method": "emulator_capture", "game": m["game"],
                "rom_sha256": m["rom_sha256"], "emulator": m["emulator"],
            },
            "artifact": {"file": m["file"], "sha256": m["sha256"], "rms": m["rms"]},
            "verification": {"non_silent": m.get("non_silent", False)},
        })

    catalog = {
        "generated_at": __import__("datetime").datetime.now().isoformat(),
        "note": ("Real SNES assets via emulator capture + curated Spriters Resource "
                 "rips (Stage 1/2). Procedural curated remains as honest fallback only."),
        "assets": bg_entries + spr_entries + audio_entries,
    }
    path = SETTINGS.root / "assets" / "catalog.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    return path


def ready_assets() -> dict[str, dict]:
    """Load catalog and return only `ready` assets (renderer contract)."""
    path = SETTINGS.asset_catalog_path
    if not path.exists():
        build_catalog()
    data = json.loads(path.read_text(encoding="utf-8"))
    return {a["asset_id"]: a for a in data["assets"] if a["status"] == "ready"}
