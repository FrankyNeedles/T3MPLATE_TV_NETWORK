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
    # Real curated frames (mario/bowser/yoshi) may exceed the 16-colour
    # procedural subpalette; they pass with real_art=True. Every frame must
    # be a real, non-blank image either way.
    is_real = bank.is_real(kind, "idle")
    gate = assets.gate_image(img, real_art=is_real)
    assert gate["all_passed"], (kind, gate, is_real)
    if not is_real:
        assert gate["checks"]["used_colors"] <= 15   # procedural SNES subpalette


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
    # every shipped asset carries HONEST provenance: real assets are tagged
    # emulator_capture (with rom_sha256) or curated_rip (with source_url);
    # only genuine placeholders remain procedural_curated.
    real_assets = [a for a in data["assets"]
                   if a["provenance"]["method"] in ("emulator_capture", "curated_rip")]
    assert real_assets, "Stage 1 must ship real (captured/curated) assets"
    for a in real_assets:
        if a["provenance"]["method"] == "emulator_capture":
            assert a["provenance"].get("rom_sha256"), a["asset_id"]
        else:  # curated_rip
            assert a["provenance"].get("source_url"), a["asset_id"]
    # soundness: nothing ready is flat/blank/noise. Video assets carry a
    # noise_battery; audio carries a non_silent flag. Check whichever exists.
    for a in data["assets"]:
        if a["status"] == "ready":
            v = a["verification"]
            if "noise_battery" in v:
                assert v["noise_battery"]["all_passed"], a["asset_id"]
            elif "non_silent" in v:
                assert v["non_silent"] is True, a["asset_id"]
    assert len(ready) >= 20


def test_curated_rip_provenance_and_fallback():
    """Stage 1 contract: mario/bowser/yoshi resolve real SMW frames where a
    pose is mounted, and fall back to the procedural painter when it isn't."""
    bank = sprites.SpriteBank(1)
    assert bank.is_real("mario", "idle") is True
    assert bank.is_real("bowser", "idle") is True
    # mario idle must be the authentic overworld sprite, not a 16x20 painter
    assert bank.image("mario", "idle").size[0] >= 18
    # an unmounted pose/char degrades gracefully to a real/non-zero frame
    img = bank.image("luigi", "idle")   # no curated luigi frame -> procedural
    gate = assets.gate_image(img)
    assert gate["all_passed"]


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