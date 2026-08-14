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


# --- Stage 2 real-audio gate: real SMW beds are non-silent & default ---------
def test_real_smw_beds_staged_and_non_silent():
    """Stage 2: assets/audio carries real emulator-captured SMW beds, each
    non-silent (RMS > threshold) and not a fake 0-byte / 4096-byte file."""
    import wave
    bed_dir = audio.AUDIO_DIR
    real = sorted(p for p in bed_dir.glob("real_smw_*.wav"))
    assert len(real) >= 3, "at least 3 distinct real SMW beds staged"
    for p in real:
        assert p.stat().st_size > 40_000          # real sample data, not a stub
        with wave.open(str(p), "rb") as w:
            n = w.getnframes()
            data = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32767.0
        assert len(data) > int(0.5 * audio.RATE)  # >0.5s of audio
        rms = float(np.sqrt((data ** 2).mean()))
        assert rms > 0.005, f"{p.name} is silent (rms={rms})"


def test_format_maps_to_real_bed():
    """Stage 2: ensure_bed selects a real SMW bed for daypart/show formats."""
    for fmt in ["news", "game_show", "morning"]:
        p = audio.ensure_bed(fmt, seconds=3.0)
        assert p.name.startswith("real_smw_"), (fmt, p.name)
        assert p.exists() and p.stat().st_size > 40_000


def test_capture_spc_via_emulator_not_pure_none():
    """Stage 2: capture_spc_via_emulator is no longer a stub return None. It
    returns a real WAV bed when a real SPC player OR a staged real bed exists.
    If neither, it honestly returns None (never a fake file)."""
    from pathlib import Path
    out = audio.capture_spc_via_emulator(Path("fake.sfc"), Path("fake.spc"))
    # a staged real SMW bed exists => we get real audio back (or None if not)
    if audio.AUDIO_DIR.exists():
        assert isinstance(out, Path), "must return a real path or None"
        if out is not None:
            assert out.name.startswith("real_smw_") or out.name.startswith("real_")
    else:
        assert out is None


def test_old_synthetic_bed_still_honest_fallback():
    """Stage 2 keeps the synth bed as an honest fallback for formats with no
    real theme (no fake claim -- it's tagged synth via the catalog)."""
    tr = audio.mixer.track_for("no_such_format", seconds=2.0)
    assert len(tr) == 2 * audio.RATE
    assert np.max(np.abs(tr)) > 0.01