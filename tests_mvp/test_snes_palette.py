"""Tests for Improvement 3 -- renderer SNES-palette quantization + per-airing
background variation.

Verifies that (a) rendered frames are quantized to SNES 15-bit palette (no
RetroArch interpolation artifacts leak through) and (b) consecutive airings of
the same slot pick DIFFERENT backgrounds (breaking the 2-unique-MD5 byte loop
documented in research_findings_visual.md section 5.7).

See research_findings_visual.md section 2.2 (background color fidelity) and
5.7 (24/7 loop is byte-identical).
"""
import numpy as np

from tvn import gary, programming, renderer
from tvn.world import LivingWorld


def _render_segment(seg, frames=1):
    """Render a segment to a list of RGB frame arrays (native res)."""
    r = renderer.Renderer()
    out = []
    for i in range(frames):
        img = r.frame(seg, i)
        out.append(np.array(img.convert("RGB")))
    return out


def _opaque_pixels(arr: np.ndarray):
    """Return non-black pixel rows (skip the black borders)."""
    flat = arr.reshape(-1, 3)
    return flat[np.any(flat != 0, axis=1)]


# ---- (a) SNES 15-bit quantization ---------------------------------------
def test_rendered_frame_is_snes_palette():
    """Every non-black pixel channel in a rendered frame must be div-by-8
    (valid SNES 15-bit). The old backgrounds leaked 20K interpolated colors."""
    world = LivingWorld("sqlite:///:memory:")
    g = gary.GaryPD(world)
    slot = programming.Slot(60, "daytime", "The News", "news", 60)
    seg = g.decide(slot, seed=0)
    frames = _render_segment(seg, frames=1)
    px = _opaque_pixels(frames[0])
    bad = [int(c) for c in px.ravel() if c != 0 and c % 8 != 0]
    assert not bad, f"non-SNES palette channels found: {bad[:10]}"


# ---- (b) per-airing background variation --------------------------------
def test_consecutive_airings_have_different_backgrounds():
    """Two airings of the same slot (different seeds) must produce frames that
    differ in their background region -- breaking the byte-identical 2-MD5 loop."""
    world = LivingWorld("sqlite:///:memory:")
    g = gary.GaryPD(world)
    slot = programming.Slot(60, "daytime", "The News", "news", 60)
    seg1 = g.decide(slot, seed=0)
    seg2 = g.decide(slot, seed=12345)
    assert seg1.background != seg2.background

    f1 = _render_segment(seg1, frames=1)[0]
    f2 = _render_segment(seg2, frames=1)[0]
    # compare a background-dominant region (upper frame, rows 0-160; this is
    # where news_studio's cyclorama sky vs studio's dark backdrop differ, and
    # the floor band rows 160-223 is identical between constructed sets).
    region = slice(0, 160), slice(0, 256)
    r1 = f1[region]
    r2 = f2[region]
    # count pixels where any channel differs (avoids int-truncation of a ratio)
    diff_pixels = int(np.any(r1 != r2, axis=2).sum())
    assert diff_pixels > 0, "consecutive airings produced identical background frames"


def test_more_than_two_unique_frames_in_run():
    """A short run seeds 3+ distinct segment backgrounds (the 2-loop is dead)."""
    world = LivingWorld("sqlite:///:memory:")
    g = gary.GaryPD(world)
    slot = programming.Slot(60, "daytime", "The News", "news", 60)
    backgrounds = set()
    for seed in range(16):
        seg = g.decide(slot, seed=seed)
        backgrounds.add(seg.background)
    assert len(backgrounds) >= 3, f"only {len(backgrounds)} unique backgrounds across 16 seeds (2-loop bug)"
