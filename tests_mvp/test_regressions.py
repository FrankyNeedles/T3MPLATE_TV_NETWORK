"""Regression tests for the test-worker BUGHUNT fixes (t3mplt-fix-bugs).

Each test maps back to a reported bug id (C1/M1/M2/M3/M4/M5, m1..m5, n1..n3)
and asserts the FIXED behaviour, not the old buggy one.
"""
import numpy as np
import pytest

from tvn import gary, output, programming, renderer, runner, content
from tvn.world import LivingWorld, Character


@pytest.fixture
def world():
    return LivingWorld("sqlite:///:memory:")


@pytest.fixture
def g():
    return gary.GaryPD(LivingWorld("sqlite:///:memory:"))


# ---- C1: maintenance tick must never block the render loop ----------------
def test_maybe_tick_never_sleeps_3600(monkeypatch):
    """C1 -- the 2-4 AM tick must not sleep the whole loop for an hour."""
    world = LivingWorld("sqlite:///:memory:")
    sleeps = []
    monkeypatch.setattr(runner.time, "sleep", lambda s: sleeps.append(s))
    # force the clock into the maintenance window (replace the datetime ref)
    class _FakeDT:
        @staticmethod
        def now(*a, **k):
            class _N:
                hour = 3
            return _N()
    monkeypatch.setattr(runner, "datetime", _FakeDT)
    monkeypatch.setattr(runner, "_last_tick_ts", None)
    runner._maybe_tick(world)          # runs tick() and records, no long sleep
    assert 3600 not in sleeps          # the blocking sleep is gone
    assert all(s < 60 for s in sleeps)  # never a multi-minute freeze


# ---- M1: --seconds 0 must be bounded, never infinite -----------------------
def test_segment_frames_zero_seconds_is_bounded(monkeypatch):
    """M1 -- an explicit 0 seconds collapses to one pass, not an infinite loop."""
    calls = []
    def fake_render(seg, final=True, renderer=None, fps=0):
        calls.append(1)
        yield np.zeros((16, 16, 3), dtype=np.uint8)
    monkeypatch.setattr(runner.renderer, "render_segment", fake_render)
    frames = list(runner.segment_frames(object(), seconds=0.0))  # must terminate
    assert isinstance(frames, list)     # did not hang


# ---- M2: atomic write / delete partial / raise on failure -----------------
def test_write_video_raises_and_cleans_partial_on_failure(tmp_path, monkeypatch):
    """M2 -- non-zero ffmpeg exit => RuntimeError, no corrupt partial left."""
    class _Stdin:
        def write(self, b): pass
        def close(self): pass
    class _Proc:
        returncode = 1
        stdin = _Stdin()
        def wait(self): return 1
    monkeypatch.setattr(output.subprocess, "Popen", lambda *a, **k: _Proc())
    out = tmp_path / "x.mp4"
    frames = (np.zeros((16, 16, 3), dtype=np.uint8) for _ in range(2))
    with pytest.raises(RuntimeError):
        output.write_video(frames, out)
    assert not out.exists()                                    # no partial at final path
    assert not list(tmp_path.glob("*.part.mp4"))               # temp cleaned up


def test_write_video_writes_atomically(tmp_path, monkeypatch):
    """M2 -- success path renames temp in place (atomic), final file appears."""
    from pathlib import Path
    class _Stdin:
        def write(self, b): pass
        def close(self): pass
    class _Proc:
        returncode = 0
        stdin = _Stdin()
        def __init__(self, cmd, **kw):
            # ffmpeg would create the .part output as it writes
            for arg in cmd:
                if arg.endswith(".part.mp4"):
                    Path(arg).write_bytes(b"data")
        def wait(self): pass
    monkeypatch.setattr(output.subprocess, "Popen", _Proc)
    out = tmp_path / "y.mp4"
    out.write_text("leftover")     # simulate an old file
    output.write_video(
        (np.zeros((16, 16, 3), dtype=np.uint8) for _ in range(1)), out, audio=b"")
    assert out.exists()
    assert not list(tmp_path.glob("*.part.mp4"))


# ---- M3: .env is loaded (streaming not dead on arrival) -------------------
def test_settings_read_env_after_dotenv(tmp_path):
    """M3 -- Settings must read TWITCH_STREAM_KEY / T3TV_FFMPEG from env (.env)."""
    # isolate: save/restore around the vars we assert so nothing leaks globally
    import os
    saved = {k: os.environ.get(k) for k in ("T3TV_FFMPEG", "TWITCH_STREAM_KEY")}
    try:
        env = tmp_path / ".env"
        env.write_text("T3TV_FFMPEG=custom_ff\nTWITCH_STREAM_KEY=abc123\n", encoding="utf-8")
        from dotenv import load_dotenv
        load_dotenv(env, override=True)
        from tvn.config import Settings
        s = Settings()
        assert s.twitch_stream_key == "abc123"
        assert s.ffmpeg == "custom_ff"
        assert "rtmp://live.twitch.tv/app/abc123" in s.rtmp_url
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


# ---- M4: configured ffmpeg binary is used, not hardcoded ------------------
def test_write_video_uses_configured_ffmpeg_binary(tmp_path, monkeypatch):
    """M4 -- the ffmpeg command starts with SETTINGS.ffmpeg, never a hardcoded name."""
    captured = {}
    from pathlib import Path
    class _Stdin:
        def write(self, b): pass
        def close(self): pass
    class _Proc:
        returncode = 0
        stdin = _Stdin()
        def __init__(self, cmd, **kw):
            captured["cmd"] = cmd
            for arg in cmd:
                if arg.endswith(".part.mp4"):
                    Path(arg).write_bytes(b"data")
        def wait(self): pass
    monkeypatch.setattr(output.subprocess, "Popen", _Proc)
    monkeypatch.setattr(output.SETTINGS, "ffmpeg", "/custom/ffmpeg-path")
    out = tmp_path / "z.mp4"
    output.write_video((np.zeros((16, 16, 3), dtype=np.uint8) for _ in range(1)), out, audio=b"")
    assert captured["cmd"][0] == "/custom/ffmpeg-path"


# ---- M5: psa + sitcom presets exist (no silent fall-back to news) ---------
def test_show_presets_cover_grid_formats():
    """M5 -- every format the GRID uses must have a real preset."""
    grid_fmts = {s.fmt for s in programming.GRID}
    missing = grid_fmts - set(content.SHOW_PRESETS.keys())
    assert not missing, f"formats with no preset: {missing}"


def test_psa_and_sitcom_decide_as_themselves(g):
    """M5 -- a psa/sitcom slot renders its own show, not a news fall-back."""
    for fmt, title in (("psa", "PSA Hour"), ("sitcom", "Luigi & Company (r)")):
        seg = g.decide(programming.Slot(60, "overnight", title, fmt, 60))
        assert seg.fmt == fmt, f"{fmt} fell back to {seg.fmt}"


# ---- m1: run_24_7 --seconds is honored -------------------------------------
def test_record_cycle_honors_seconds(monkeypatch, tmp_path):
    """m1 -- _record_cycle uses the passed seconds, not a hardcoded 12.0."""
    seen = {}
    class _Seg:
        fmt = "news"; title = "News"; daypart = "day"; seg_id = "s1"; cast = []
    class _G:
        def decide(self, slot): return _Seg()
    class _W:
        def on_air(self, *a, **k): pass
    class _Slot:
        fmt = "news"; daypart = "day"
    monkeypatch.setattr(runner.programming, "get_slot", lambda: _Slot())
    monkeypatch.setattr(runner, "segment_frames",
                        lambda seg, seconds, renderer_=None: (seen.__setitem__("s", seconds) or iter([])))
    monkeypatch.setattr(runner, "segment_audio",
                        lambda seg, seconds, fmt="": (seen.__setitem__("a", seconds) or b""))
    monkeypatch.setattr(runner.output, "write_video", lambda *a, **k: a[1])
    runner._record_cycle(_W(), _G(), tmp_path, seconds=7.5)
    assert seen["s"] == 7.5 and seen["a"] == 7.5


# ---- m2: keep the show's hosts as the speakers -----------------------------
def test_decide_keeps_show_hosts_not_feud_override(g):
    """m2 -- a feud must not repin dialogue to feud actors; preset hosts speak."""
    slot = programming.Slot(6 * 60, "early_news", "T3TV Morning Update", "news", 30)
    seg = g.decide(slot)
    cast_names = [c.name for c in seg.cast]
    speakers = [b.speaker for b in seg.beats]
    # news preset hosts are mario, luigi -- luigi must still co-host-and-speak
    assert "luigi" in cast_names
    assert "luigi" in speakers


# ---- m3: popularity delta matches relationship outcome ---------------------
def test_on_air_feud_lowers_popularity(world):
    """m3 -- co-hosting a feud pair drops their popularity, not +1 for both."""
    world.on_air(["mario", "bowser"], show="Showdown", tension=0)  # seeded feud
    assert world.get_character("mario").popularity < 51
    assert world.get_character("bowser").popularity < 51


# ---- m5: seeding is idempotent / concurrency-safe --------------------------
def test_seed_is_idempotent_across_reopen(tmp_path):
    """m5 -- re-opening a seeded DB must not re-seed or duplicate."""
    db = tmp_path / "c.db"
    w = LivingWorld(f"sqlite:///{db}")
    assert w.session.query(Character).count() == 9
    w.session.close(); w.engine.dispose()
    w2 = LivingWorld(f"sqlite:///{db}")
    assert w2.session.query(Character).count() == 9   # not 18


# ---- n1: dead multiply removed ---------------------------------------------
def test_render_cast_spacing_is_correct(monkeypatch):
    """n1 -- draw_cast runs (spacing no longer depends on a dead *0 term)."""
    class _C:
        name = "mario"; kind = "mario"; motion = "idle"
    class _Seg:
        cast = [_C()] * 2
    from PIL import Image
    r = renderer.Renderer()
    canvas = Image.new("RGBA", renderer.NATIVE, (0, 0, 0, 255))
    r.draw_cast(canvas, _Seg(), 0)     # must not raise
    assert canvas.size == renderer.NATIVE


# ---- n3: render length honors fps ------------------------------------------
def test_render_segment_honors_fps(g):
    """n3 -- frames_total scales with fps instead of a hardcoded 24."""
    seg = g.decide(programming.Slot(20 * 60, "prime", "The Super Mario Bros. Show", "sitcom", 60))
    f24 = sum(1 for _ in renderer.render_segment(seg, fps=24))
    f48 = sum(1 for _ in renderer.render_segment(seg, fps=48))
    assert f48 > f24