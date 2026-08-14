"""Stage 7 A/V + hygiene regression tests (green gate: real audio+video sync).

Maps to audit F-2.5 (audio byte-identical within a slot), WEAK-3 (`--stream`
was video-only), and BUG-1 (silent dead push). Each test guards a fixed
behaviour, not a hand-run claim.
"""
import numpy as np
import pytest

from tvn import audio, output
from tvn.config import SETTINGS


# ---- F-2.5: same-slot consecutive airings differ in AUDIO -------------------
def test_same_slot_airings_differ_in_audio_with_variant():
    """Audit F-2.5: the audio cache key now includes a per-airing `variant`, so
    two airings of the SAME fmt in the SAME slot carry DIFFERENT audio (the old
    cache was fmt:seconds only -> byte-identical). Real bed must be non-trivial
    in length for the phase-rotation to be meaningful."""
    mixer = audio.Mixer()
    a0 = mixer.track_for("news", seconds=6.0, variant=0)
    a1 = mixer.track_for("news", seconds=6.0, variant=1)
    a2 = mixer.track_for("news", seconds=6.0, variant=2)
    # same duration, all real audio -- but pairwise distinct (not byte-identical)
    assert len(a0) == len(a1) == len(a2) == 6 * audio.RATE
    assert not np.array_equal(a0, a1), "variant 0 vs 1 must differ in audio"
    assert not np.array_equal(a1, a2), "variant 1 vs 2 must differ in audio"
    # and they're all genuinely non-silent real audio
    for tr in (a0, a1, a2):
        assert np.max(np.abs(tr)) > 0.01


def test_same_variant_is_cached_and_stable():
    """Same fmt+seconds+variant returns the same (cached) audio; the novelty is
    per-airing variant, not nondeterminism -- so a single airing is stable."""
    mixer = audio.Mixer()
    x = mixer.track_for("news", seconds=3.0, variant=7)
    y = mixer.track_for("news", seconds=3.0, variant=7)
    assert np.array_equal(x, y)


# ---- A/V sync bound (F-2.5 / BUG-1) -----------------------------------------
def test_av_sync_ok_true_within_tolerance():
    assert output._av_sync_ok(6 * 22050, 6 * 24, 24, 22050) is True
    assert output._av_sync_ok(6 * 22050 - 200, 6 * 24, 24, 22050) is True
    # a gross mismatch (e.g. 15 s of audio vs 6 s of video) must fail
    assert output._av_sync_ok(15 * 22050, 6 * 24, 24, 22050) is False


def test_pad_audio_to_exact_frame_count():
    """write_video bounds audio to the exact video frames: short audio is
    zero-padded, long audio is trimmed, to lock duration."""
    fps, rate = 24, 22050
    want = int(round(6 * rate)) * 2                 # 6s audio @rate -> exact bytes
    short = b"\x11\x22" * (want // 2 - 100)            # 100 samples too short
    padded = output._pad_audio_to_frames(short, 6 * fps, fps, rate)
    assert len(padded) == want
    long = b"\x11\x22" * (want // 2 + 100)
    trimmed = output._pad_audio_to_frames(long, 6 * fps, fps, rate)
    assert len(trimmed) == want
    # zero-padding leaves the real audio intact at the front
    assert padded[: len(short)] == short


@pytest.mark.skipif(
    pytest.importorskip("shutil").which("ffmpeg") is None, reason="ffmpeg not on PATH")
def test_write_video_av_locked(tmp_path):
    """End-to-end: write_video produces a playable mp4 whose audio and video
    durations are locked within 0.2 s (real ffmpeg)."""
    rng = np.random.default_rng(1)
    seconds = 6.0
    frames = (rng.integers(0, 255, (448, 512, 3), dtype=np.uint8)
              for _ in range(int(seconds * SETTINGS.rate)))
    bed = audio.Mixer().track_for("news", seconds=seconds, variant=1)
    aud = output.raw_audio_bytes(bed)
    path = output.write_video(frames, tmp_path / "av.mp4", audio=aud, rate=audio.RATE)
    import subprocess
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "stream=codec_type,duration", "-show_entries", "format=duration",
         "-of", "json", str(path)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    import json
    info = json.loads(r.stdout)
    streams = {s["codec_type"]: float(s["duration"]) for s in info["streams"]}
    assert "video" in streams and "audio" in streams
    assert abs(streams["audio"] - streams["video"]) < 0.2, streams
    assert abs(streams["video"] - seconds) < 0.2, streams


# ---- WEAK-3 / BUG-1: RTMP push is audio+video, and a dead push is loud ------
def _fake_proc(capture):
    class _Stdin:
        def write(self, b):
            capture.setdefault("written", b"")
            capture["written"] += b
        def close(self):
            capture["closed"] = True
    class _Proc:
        returncode = 0
        def __init__(self, cmd, stdin, stdout, stderr):
            capture["cmd"] = cmd
            # stderr must be the VISIBLE sentinel (None == inherit parent), i.e.
            # it is NOT subprocess.DEVNULL (the old silent-muffle bug).
            capture["stderr_is_devnull"] = (stderr is __import__("subprocess").DEVNULL)
            self.stdin = _Stdin()
        def wait(self):
            return self.returncode
    return _Proc


def test_stream_rtmp_muxes_audio_and_keeps_stderr_visible(monkeypatch):
    """WEAK-3/BUG-1: stream_rtmp adds an aac input (audio) for `--stream`, and it
    must NEVER DEVNULL stderr -- a dead push must be loud, not silent."""
    capture = {}
    monkeypatch.setattr(output.subprocess, "Popen",
                        lambda *a, **k: _fake_proc(capture)(*a, **k))
    frames_audio = []
    rng = np.random.default_rng(2)
    one = rng.integers(0, 255, (448, 512, 3), dtype=np.uint8)
    frames_audio.append((one, b"\x00\x00" * 100))
    frames_audio.append((one, b"\x00\x00" * 100))
    output.stream_rtmp(iter(frames_audio), "rtmp://test/app/key")
    cmd = capture["cmd"]
    # an aac audio encoder IS configured => audio+video push
    assert "aac" in cmd
    assert any(a.startswith("-af") for a in cmd)
    assert any(a.startswith("aresample") or "aresample" in a for a in cmd)
    # stderr is surfaced (None == inherit parent, i.e. visible), not DEVNULL
    assert capture["stderr_is_devnull"] is False   # stderr surfaced, not muffled
    assert all(b not in cmd for b in ["-v", "quiet"])  # not muted


def test_stream_rtmp_pair_form_writes_locked_av(monkeypatch):
    """The (frame, pcm_chunk) pair form writes frame bytes THEN that frame's
    audio chunk (A/V lock), and tolerates the push being interrupted."""
    seen = {"writes": []}
    class _S:
        def write(self, b):
            seen["writes"].append(b)
        def close(self):
            pass
    class _P:
        returncode = 0
        stdin = _S()
        def __init__(self, cmd, stdin, stdout, stderr):
            self.stdin = _S()
        def wait(self):
            return 0
    monkeypatch.setattr(output.subprocess, "Popen", lambda *a, **k: _P(*a, **k))
    rng = np.random.default_rng(3)
    one = rng.integers(0, 255, (448, 512, 3), dtype=np.uint8)
    chip_frames = [(one, b"AAA"), (one, b"BBB"), (one, b"CCC")]
    out = output.stream_rtmp(iter(chip_frames), "rtmp://test/app/k")
    assert out == 0
    # 3 frames -> frame_bytes,A; frame_bytes,B; frame_bytes,C
    assert len(seen["writes"]) == 6
    assert b"AAA" in seen["writes"][1] and b"BBB" in seen["writes"][3]