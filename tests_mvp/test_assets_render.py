"""Asset kit & headless renderer tests (substance-over-slop gates)."""
import json
import numpy as np
import pytest

from tvn import sprites, assets, renderer, broadcast, content
from tvn.animation import library, BASE_MOTIONS


@pytest.mark.parametrize("kind", list(sprites.CAST.keys()))
def test_all_cast_pass_noise_gates(kind):
    bank = sprites.SpriteBank(1)
    img = bank.image(kind, "idle")
    gate = assets.gate_image(img)
    assert gate["all_passed"], (kind, gate)
    assert gate["checks"]["used_colors"] <= 15   # SNES 16-colour subpalette discipline


@pytest.mark.parametrize("set_name", ["news_studio", "talk_show", "diner",
                                      "city", "sports_arena", "game_show"])
def test_backgrounds_render(set_name):
    img = assets.background(set_name)
    assert img.size == (256, 224)
    arr = np.asarray(img.convert("RGB"))
    assert arr.mean() > 10  # not blank


def test_catalog_builds_all_ready():
    path = assets.build_catalog()
    data = json.loads(path.read_text(encoding="utf-8"))
    ready = {a["asset_id"]: a for a in data["assets"] if a["status"] == "ready"}
    # every shipped asset must be honest (procedural, not claimed ROM rip)
    for a in data["assets"]:
        assert a["provenance"]["method"] == "procedural_curated"
    assert len(ready) >= 15


def test_movement_library_cache_and_fallback():
    assert "walk" in BASE_MOTIONS
    poses, fps, loop = library.play("mario", "walk")
    assert poses in (("walk_a", "walk_b"),) and loop
    # movement library: unknown MOTION always falls back to idle (no crash)
    poses, _, _ = library.play("unknown_char", "no_such_motion")
    assert poses == ("idle",)
    # a known motion is available to every character (base set)
    poses, _, loop = library.play("unknown_char", "walk")
    assert poses == ("walk_a", "walk_b") and loop


@pytest.fixture
def segment():
    return broadcast.BroadcastSegment(
        seg_id="t", title="News at 11", fmt="news", daypart="late_news",
        background="news_studio",
        cast=[broadcast.Cast(name="mario", kind="mario", title="Anchor", motion="idle"),
              broadcast.Cast(name="luigi", kind="luigi", title="Co-Anchor", motion="idle")],
        beats=[broadcast.Beat(speaker="mario", text="Great to be on the air tonight.")],
        ticker=["Breaking: warp pipe reopened"])


def test_renderer_produces_non_blank_frames(segment):
    frames = list(renderer.render_segment(segment, final=True))
    assert len(frames) > 24
    for f in frames:
        assert f.shape == (448, 512, 3)      # 256x224 scaled x2
        arr = f.astype(np.float32)
        assert arr.mean() > 20 and arr.std() > 15  # not blank/black
    # movement/typewriter actually changes pixels between frames
    a = np.asarray(frames[len(frames) // 2])
    b = np.asarray(frames[-1])
    assert not np.array_equal(a, b)


def test_promo_card_is_full_screen(segment):
    r = renderer.Renderer()
    frame = r.draw_full("commercial", "Mushroom Cola", "T3TV")
    assert frame.size == (256, 224)