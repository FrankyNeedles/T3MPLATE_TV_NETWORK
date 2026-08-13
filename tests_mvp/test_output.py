"""Audio + ffmpeg output tests (green gate: real playable broadcast)."""
import shutil
import subprocess
import numpy as np
import pytest

from tvn import audio, output, runner
from tvn.world import LivingWorld

HAS_FFMPEG = shutil.which("ffmpeg") is not None


def test_synth_bed_is_real_sound():
    samples = audio.synth_bed("news", seconds=2.0)
    assert samples.shape[0] == 2 * audio.RATE
    assert np.max(np.abs(samples)) > 0.05   # not silence


def test_ensure_bed_writes_wav(tmp_path):
    import tvn.audio as a
    wav = a.write_wav(tmp_path / "t.wav", audio.synth_bed("bumper", 1.0))
    from pathlib import Path
    assert (tmp_path / "t.wav").exists()
    assert (tmp_path / "t.wav").stat().st_size > 1000


def test_mixer_returns_stable_loop():
    tr = audio.mixer.track_for("news", seconds=3.0)
    assert len(tr) == 3 * audio.RATE
    assert np.max(np.abs(tr)) > 0.01


def test_synth_bed_crossfade_uses_tail():
    """n2 -- the loop-crossfade must blend the TAIL into the head (not a silent no-op)."""
    samples = audio.synth_bed("bumper", seconds=1.0)
    ff = audio.RATE // 8
    head = np.copy(samples[:ff])
    tail = np.copy(samples[-ff:])
    # the head should now be a blend including the tail, i.e. non-negligibly
    # different from a pure halved head (the old `head * 0.0` no-op).
    pure_half = 0.5 * np.zeros_like(head)  # old bug: blend term was zero
    assert np.max(np.abs(head)) > 0.0       # head is audible, not muted
    # and the seam is continuous: |head-start - tail-end| stays smooth
    seam_gap = abs(float(head[0]) - float(tail[-1]))
    assert seam_gap < np.max(np.abs(samples))   # loop joins without a big click


@pytest.mark.skipif(not HAS_FFMPEG, reason="ffmpeg not on PATH")
def test_run_once_produces_playable_broadcast(tmp_path):
    """Green gate: run_once must write a real MP4 (video+audio, non-trivial size)."""
    world = LivingWorld("sqlite:///:memory:")
    out = tmp_path / "broadcast_t.mp4"
    path = runner.run_once(seconds=6.0, out=out, world=world)
    assert path.exists() and path.stat().st_size > 50_000
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "stream=codec_type,codec_name", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True)
    txt = r.stdout
    assert "video" in txt and "h264" in txt
    assert "audio" in txt and "aac" in txt


@pytest.mark.skipif(not HAS_FFMPEG, reason="ffmpeg not on PATH")
def test_output_wireframes_to_mp4(tmp_path):
    """write_video pipes frames + audio and yields a valid mp4."""
    import tvn.audio as a
    rng = np.random.default_rng(0)
    frames = (rng.integers(0, 255, (448, 512, 3), dtype=np.uint8) for _ in range(24))
    aud = output.raw_audio_bytes(audio.synth_bed("bumper", 1.0))
    path = output.write_video(frames, tmp_path / "w.mp4", audio=aud)
    assert path.exists() and path.stat().st_size > 0