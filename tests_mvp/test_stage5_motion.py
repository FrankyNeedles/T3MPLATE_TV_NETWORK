"""Stage 5 (FINISH MOTION) tests -- the audit's highest-priority wiring fixes:

* F-1.1  feed Beat.motion into the renderer so on-air cast actually animates
         (no more every-Cast-is-idle frozen frame), cadence driven by beat
         duration, and walk motion is a real cross-slot slide.
* F-1.4  the real_art gate rejects un-keyed / corner-opaque / near-100% boxes.
* F-3.1  on_air upserts a Show from a grid-slot title so episode_count/title/
         rating advance in a live-style run (not only tested seeded names).
* F-3.2  relationship arcs backfill idempotently on an existing persistent DB.
"""
import numpy as np
import pytest

from PIL import Image

from tvn import broadcast, renderer, programming, assets, content
from tvn.world import LivingWorld, Show, Character, Relationship
from tvn.animation import library


# ---- F-1.1: on-air animation is driven by Beat.motion ---------------------
def _motion_segment(motion="talk"):
    return broadcast.BroadcastSegment(
        seg_id="m", title="Stage Test", fmt="news", daypart="day",
        background="studio",
        cast=[broadcast.Cast(name="luigi", kind="luigi", title="Host"),
              broadcast.Cast(name="toad", kind="toad", title="Co")],
        beats=[broadcast.Beat(speaker="luigi", text="Testing our movement library today, folks.",
                              motion=motion, frames=180)])


def test_renderer_uses_beat_motion_not_frozen_cast_motion():
    """F-1.1 -- the active beat's speaker animates with the beat's motion; a
    painter-only cast member (luigi) must NOT be stuck in idle when the beat
    calls for talk/happy/walk."""
    r = renderer.Renderer()
    seg = _motion_segment(motion="happy")
    beat, _ = r.active_beat(seg, 40)
    assert beat is not None
    c = next(c for c in seg.cast if c.name == "luigi")
    assert r._motion_for(c, beat) == "happy"
    # non-speaker stays idle
    other = next(c for c in seg.cast if c.name == "toad")
    assert r._motion_for(other, beat) == "idle"


@pytest.mark.parametrize("motion", ["talk", "happy", "walk"])
def test_active_beat_cadence_driven_by_beat_duration(motion):
    """F-1.1 -- the active beat is selected by CUMULATIVE beat length (beat.frames),
    not a static frame//90 slide; the beat-local frame advances within it."""
    r = renderer.Renderer()
    seg = broadcast.BroadcastSegment(
        seg_id="m", title="T", fmt="news", background="studio",
        cast=[broadcast.Cast(name="mario", kind="mario"),
              broadcast.Cast(name="luigi", kind="luigi")],
        beats=[
            broadcast.Beat(speaker="mario", text="First line here.", motion="talk", frames=120),
            broadcast.Beat(speaker="luigi", text="Second line here.", motion="happy", frames=60),
        ])
    b0, _ = r.active_beat(seg, 20)      # inside beat 0 (frames 0..119)
    b1, local = r.active_beat(seg, 130)  # inside beat 1 (frames 120..179)
    assert b0.speaker == "mario"
    assert b1.speaker == "luigi"
    assert 0 <= local < 60


def test_walk_motion_produces_real_horizontal_movement():
    """F-1.1 acceptance-1 -- a walk beat slides the cast member across the slot,
    so consecutive frames show genuine pixel motion, not a static pose."""
    r = renderer.Renderer()
    seg = _motion_segment(motion="walk")
    canvas_a = Image.new("RGBA", renderer.NATIVE, (0, 0, 0, 255))
    canvas_b = Image.new("RGBA", renderer.NATIVE, (0, 0, 0, 255))
    r.draw_cast(canvas_a, seg, 0, beat=seg.beats[0], walk_offset=-20.0)
    r.draw_cast(canvas_b, seg, 0, beat=seg.beats[0], walk_offset=+20.0)
    a = np.asarray(canvas_a.convert("RGB")).astype(int)
    b = np.asarray(canvas_b.convert("RGB")).astype(int)
    assert np.abs(a - b).sum() > 0, "walk_offset must translate the cast member"


def test_render_segment_has_motion_between_show_frames():
    """F-1.1 acceptance-1 -- rendering a show with a talk beat changes pixels
    frame-to-frame (the old feed was a static idle pose)."""
    seg = _motion_segment(motion="talk")
    frames = list(renderer.render_segment(seg, final=True, renderer=renderer.Renderer()))
    assert len(frames) > 24
    a = np.asarray(frames[len(frames) // 2])
    b = np.asarray(frames[-1])
    assert not np.array_equal(a, b), "show frames are byte-identical (no animation)"


def test_six_painter_chars_animate_when_motion_fed():
    """F-1.1 / F-1.6 -- the painter-only cast (luigi/peach/toad/wario/link/zelda)
    resolve a NON-idle pose for talk/happy/walk via the SpriteBank."""
    from tvn import sprites
    bank = sprites.SpriteBank(1)
    for kind in ("luigi", "peach", "toad", "wario", "link", "zelda"):
        for pose in ("talk_a", "happy", "walk_a"):
            img = bank.image(kind, pose)
            assert img.size[0] > 0 and img.size[1] > 0
        # walk/happy/talk must not silently collapse to the idle frame
        idle = np.asarray(bank.image(kind, "idle").convert("RGB"))
        talk = np.asarray(bank.image(kind, "talk_a").convert("RGB"))
        happy = np.asarray(bank.image(kind, "happy").convert("RGB"))
        assert talk.shape == idle.shape
        assert not np.array_equal(talk, idle), f"{kind} talk collapsed to idle"
        assert not np.array_equal(happy, idle), f"{kind} happy collapsed to idle"


# ---- F-1.4: the real_art gate rejects un-keyed / corner-opaque boxes -------
def _box(w, h, color=(255, 255, 255, 255)):
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    arr[..., 3] = 255
    arr[..., :3] = color[:3]
    return Image.fromarray(arr, "RGBA")


def test_real_art_gate_rejects_unkeyed_opaque_box():
    """F-1.4 -- a near-100%-coverage corner-opaque rectangle (the OLD Yoshi
    failure mode) must FAIL to 'ready' under the real_art gate, which previously
    certified it."""
    g = assets.gate_image(_box(40, 34), real_art=True)
    assert g["all_passed"] is False
    assert g["checks"]["corner_opaque"] >= 2       # all corners opaque


def test_real_art_gate_rejects_bottom_leak():
    """F-1.4 -- an opaque bottom-corner leak (the OLD Bowser failure mode) must be
    rejected: two opaque corners on one edge is the signature of an un-keyed base."""
    arr = np.zeros((40, 28, 4), dtype=np.uint8)
    arr[..., 3] = 0                      # transparent everywhere...
    arr[..., :3] = (0, 48, 48)
    arr[-1, 0, 3] = 255; arr[-1, -1, 3] = 255   # ...except the bottom two corners
    g = assets.gate_image(Image.fromarray(arr, "RGBA"), real_art=True)
    assert g["all_passed"] is False


def test_fixed_real_sprites_pass_the_tightened_gate():
    """F-1.4 -- the RE-KEYED yoshi/bowser frames (transparent margins) pass the
    tightened real_art gate, so they are honestly 'ready'."""
    for path, corners in [
        ("assets/movements/yoshi/yoshi_idle.png", 1),
        ("assets/movements/bowser/bowser_idle.png", 0),
        ("assets/movements/bowser/bowser_walk_a.png", 0),
        ("assets/movements/bowser/bowser_walk_b.png", 0),
    ]:
        img = Image.open(path).convert("RGBA")
        g = assets.gate_image(img, real_art=True)
        assert g["all_passed"] is True, (path, g)
        assert g["checks"]["corner_opaque"] == corners


def test_cast_catalog_yoshi_bowser_ready_after_rekey():
    """F-1.2/1.3/1.4 -- the rebuilt catalog marks the re-keyed yoshi/bowser
    frames ready (broken un-keyed box no longer slips through)."""
    import json
    from tvn.config import SETTINGS
    data = json.loads(SETTINGS.asset_catalog_path.read_text(encoding="utf-8"))
    by_id = {a["asset_id"]: a for a in data["assets"]}
    for aid in ("spr_yoshi_idle", "spr_bowser_idle"):
        assert by_id[aid]["status"] == "ready", aid


# ---- F-3.1: episode continuity advances with a real grid-slot title --------
def test_on_air_upserts_show_from_grid_slot_title(world):
    """F-3.1 -- on_air with an ACTUAL grid title (e.g. 'Super Playhouse', which
    is not a seeded 'X of T3TV' name) upserts a Show and advances its episode
    count/title/rating in the real loop."""
    before = world.session.query(Show).filter_by(name="Super Playhouse").first()
    assert before is None                     # not a seeded show
    world.on_air(["yoshi", "toad"], show="Super Playhouse", tension=0, genre="cartoon")
    s = world.session.query(Show).filter_by(name="Super Playhouse").first()
    assert s is not None
    assert s.genre == "cartoon"
    assert s.episode_count >= 1               # continuity actually advanced
    assert s.episode_title                    # a real rotating title
    assert s.rating > 0
    s1 = s.episode_count
    world.on_air(["yoshi", "toad"], show="Super Playhouse", tension=0, genre="cartoon")
    world.session.refresh(s)
    assert s.episode_count == s1 + 1


def test_grid_titles_advance_episodes_in_live_style_run(world):
    """F-3.1 -- several real GRID slot titles all advance episode counts through
    the production-style on_air path (not a single hardcoded seeded name)."""
    grid_titles = [s.title for s in programming.GRID]
    assert "Super Playhouse" in grid_titles
    # air three distinct real grid titles
    for slot in [programming.GRID[11], programming.GRID[0], programming.GRID[23]]:
        world.on_air([c for c in ["yoshi", "toad"]], show=slot.title,
                     tension=0, genre=slot.fmt)
    for slot in [programming.GRID[11], programming.GRID[0], programming.GRID[23]]:
        s = world.session.query(Show).filter_by(name=slot.title).first()
        assert s is not None, slot.title
        assert s.episode_count >= 1, slot.title


# ---- F-3.2: arcs backfill on an existing persistent DB ---------------------
def test_arcs_backfill_on_reopened_persistent_db(tmp_path):
    """F-3.2 -- a persistent DB that already exists WITHOUT arc labels (simulated
    by clearing them) gets its arcs backfilled on reopen, idempotently."""
    db = tmp_path / "m.db"
    w = LivingWorld(f"sqlite:///{db}")
    rel = w._find_rel(w.get_character("mario").id, w.get_character("bowser").id)
    assert rel.arc_label == "The Eternal Rivalry"
    # simulate the audit's live-DB state: columns exist but no arcs filled
    rel.arc_label = ""
    w.session.commit()
    w.session.close(); w.engine.dispose()
    w2 = LivingWorld(f"sqlite:///{db}")       # reopen -> migration backfill runs
    rel2 = w2._find_rel(w2.get_character("mario").id, w2.get_character("bowser").id)
    assert rel2.arc_label == "The Eternal Rivalry"
    # idempotent: re-running does not clobber
    rel2.arc_label = "Custom Detour"
    w2.session.commit()
    w2.session.close(); w2.engine.dispose()
    w3 = LivingWorld(f"sqlite:///{db}")
    rel3 = w3._find_rel(w3.get_character("mario").id, w3.get_character("bowser").id)
    assert rel3.arc_label == "Custom Detour"     # not overwritten


@pytest.fixture
def world():
    return LivingWorld("sqlite:///:memory:")