"""Tests for Improvement 1 -- asset gate dedup + SNES-15bit palette fidelity.

Verifies that gate_image() rejects (a) duplicate hashes (the 3 SMW-overworld
sets that share real_news_studio.png) and (b) backgrounds whose palette is not
SNES-15bit (the RetroArch-interpolated real_*.png with 20K colors).

See research_findings_visual.md sections 3.2 (duplicate backgrounds) and
5.3 (SNES palette gap) for the measurements being guarded.
"""
import hashlib
import json

import numpy as np
from PIL import Image
from tvn import assets


def _hash(img: Image.Image) -> str:
    return hashlib.sha256(img.convert("RGBA").tobytes()).hexdigest()


# ---- (a) dedup ---------------------------------------------------------
def test_duplicate_backgrounds_quarantined_in_catalog(tmp_path, monkeypatch):
    """The manifest has 8 entries but only 5 unique SMW screenshots
    (news_studio==city==sports_arena, cartoon_house==diner). build_catalog must
    quarantine the duplicates (research_findings_visual.md 3.2).
    """
    # stage a minimal manifest with deliberate duplicate PNGs (same bytes)
    bg_dir = tmp_path / "assets" / "backgrounds"
    bg_dir.mkdir(parents=True)
    # one SNES-valid unique image + one identical copy (the "duplicate")
    from PIL import Image
    unique = Image.new("RGBA", (256, 224), (8, 8, 24, 255))
    unique.paste((32, 96, 160, 255), (0, 0, 128, 112))  # 2nd SNES color
    unique.save(str(bg_dir / "real_unique_a.png"))
    # identical bytes -> this is the duplicate
    dup = Image.new("RGBA", (256, 224), (8, 8, 24, 255))
    dup.paste((32, 96, 160, 255), (0, 0, 128, 112))
    dup.save(str(bg_dir / "real_unique_b.png"))
    manifest = [
        {"asset_id": "bg_a", "set_name": "news_studio",
         "file": "real_unique_a.png", "game": "SNES", "rom_sha256": "x",
         "emulator": "test", "note": "test A"},
        {"asset_id": "bg_b", "set_name": "city",
         "file": "real_unique_b.png", "game": "SNES", "rom_sha256": "x",
         "emulator": "test", "note": "test B (identical pixels)"},
    ]
    (bg_dir / "manifest.json").write_text(json.dumps(manifest))

    class _FakeSettings:
        root = tmp_path
        res_native = (256, 224)
    monkeypatch.setattr(assets, "SETTINGS", _FakeSettings())
    assets.reset_gate_state()
    # blank the procedural/sprite paths that build_catalog may probe
    monkeypatch.setattr(assets, "_REAL_BG_CACHE", getattr(assets, "_REAL_BG_CACHE", {}))

    path = assets.build_catalog()
    data = json.loads(path.read_text())
    bgs = [a for a in data["assets"] if a["asset_type"] == "background"]
    dups = [b for b in bgs if b.get("gate_reason") == "duplicate"]
    assert len(dups) == 1, f"expected 1 duplicate quarantined, got {len(dups)}"


def test_distinct_backgrounds_both_pass():
    """Two genuinely different backgrounds both pass the gate."""
    assets.reset_gate_state()
    img1 = Image.new("RGBA", (256, 224), (8, 8, 24, 255))  # SNES-15bit bg
    img1.paste((32, 96, 160, 255), (0, 0, 128, 112))  # SNES accent, 2nd color
    img2 = Image.new("RGBA", (256, 224), (200, 8, 24, 255))  # different bg
    img2.paste((8, 200, 40, 255), (0, 0, 128, 112))  # SNES accent
    g1 = assets.gate_image(img1, kind="background")
    g2 = assets.gate_image(img2, kind="background")
    assert g1["all_passed"] is True
    assert g2["all_passed"] is True


# ---- (b) SNES-15bit palette fidelity -----------------------------------
def test_non_snes_palette_background_rejected():
    """A background with interpolated (non-SNES-15bit) colors must be rejected.

    SNES 15-bit channels live in {0, 8, 16, ..., 248}. The real SMW captures
    carry RetroArch scaler artifacts like RGB (0,0,1), (0,0,2)... -- non-SNES.
    """
    assets.reset_gate_state()
    img = Image.new("RGBA", (256, 224), (8, 8, 24, 255))
    # paint with a non-SNES color (channel value 5 is not div-by-8)
    img.paste((5, 5, 5, 255), (10, 10, 200, 200))
    img.paste((200, 3, 120, 255), (50, 50, 150, 150))  # 3 not div-by-8
    g = assets.gate_image(img, kind="background")
    assert g["all_passed"] is False
    assert "snes_palette_validity" in g["checks"]


def test_real_snes_palette_background_passes():
    """A background using ONLY SNES-15bit colors passes the palette gate."""
    assets.reset_gate_state()
    img = Image.new("RGBA", (256, 224), (8, 8, 24, 255))
    # all channels div-by-8 -> valid SNES 15-bit
    img.paste((32, 120, 200, 255), (10, 10, 200, 200))  # 32,120,200 all /8
    g = assets.gate_image(img, kind="background")
    assert g["all_passed"] is True
