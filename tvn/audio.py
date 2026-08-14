#!/usr/bin/env python3
"""Audio engine -- SNES music & SFX, treated first-class.

Frank flagged SNES audio as core to the 90s feel and unsure how to get it in
honestly. Per RESEARCH_SNES the honest route is **emulator capture** (play a ROM
in snes9x/RetroArch, trigger "save SPC", render the 64KB SPC to WAV with an SPC
player) -- NOT hand-rolling a static ROM decoder (that produced noise).

The MVP ships a zero-dependency **synthesized chiptune bed** (square/triangle
oscillators, honest `method:"synth"`) so the broadcast has real audible audio
today, AND a loader that transparently prefers real SPC-rendered WAVs dropped in
`assets/audio/` -- so Frank can plug the emulator-capture route in later without
changing the broadcast code.
"""
from __future__ import annotations

import wave
import struct
import hashlib
from pathlib import Path
from typing import Optional

import numpy as np

from .config import SETTINGS

RATE = 22050
AUDIO_DIR = SETTINGS.root / "assets" / "audio"


# --- honest synth beds (chiptune approximation; method:"synth") --------------
def _osc(phase, wave="square"):
    if wave == "square":
        return np.sign(np.sin(phase))
    return -1 + 2 * (2 * ((phase / (2 * np.pi)) % 1)) - 1  # triangle-ish


def synth_bed(track: str, seconds: float = 12.0, rate: int = RATE) -> np.ndarray:
    """Generate a short looped chiptune bed for a track id. Pure numpy."""
    t = np.linspace(0, seconds, int(seconds * rate), endpoint=False)
    # note grid in a 90s-ISP key (upbeat, cheap-sounding, cheerful)
    bass = np.array([196, 220, 261, 196, 220, 196, 147, 196])
    lead = np.array([523, 659, 784, 659, 523, 659, 784, 880])
    out = np.zeros_like(t)
    for i, i0 in enumerate(range(0, int(seconds * rate), rate // 4)):
        if i0 >= len(t):
            break
        seg = t[i0:i0 + rate // 4] if i0 + rate // 4 <= len(t) else t[i0:]
        if len(seg) == 0:
            continue
        freq_b = bass[i % len(bass)]
        freq_l = lead[i % len(lead)]
        env = np.exp(-2.0 * np.linspace(0, 1, len(seg)))  # pluck envelope
        out[i0:i0 + len(seg)] += (0.30 * env * np.sign(np.sin(2 * np.pi * freq_b * seg))
                                  + 0.18 * env * np.sin(2 * np.pi * freq_l * seg))
    # normalize to a sane broadcast level
    peak = np.max(np.abs(out)) or 1.0
    out = (out / peak) * 0.6
    # loop continuity: crossfade tail into head so it loops cleanly.
    # (n2) the old line used `head * 0.0`, zeroing the blend -- a no-op. Use the
    # actual tail clip so the loop seam is a real fade, not a silent edge cut.
    ff = rate // 8
    tail = np.copy(out[-ff:])
    out[:ff] = 0.5 * (out[:ff] + tail)
    return out


def write_wav(path: Path, samples: np.ndarray, rate: int = RATE):
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(samples, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())


def ensure_bed(track: str, seconds: float = 12.0) -> Path:
    """Return an on-disk WAV for a track.

    Real-emulator-captured beds (`real_smw_*.wav`) win over synthesized beds
    whenever a matching real file exists; otherwise the honest synth chiptune
    bed is written. `track` may be a bare name or a `real_*` id.
    """
    track = (track or "bumper").split(".")[0]
    # real bed resolution: prefer a `real_<track>.wav` / `real_smw_*.wav`
    for cand in _real_bed_candidates(track):
        if cand.exists():
            return cand
    path = AUDIO_DIR / f"bed_{track}.wav"
    if not path.exists():
        write_wav(path, synth_bed(track, seconds))
    return path


def _real_bed_candidates(track: str) -> list[Path]:
    """Candidate real-capture files for a track id, most-specific first."""
    out = []
    if track.startswith("real_"):
        out.append(AUDIO_DIR / f"{track}.wav")
        out.append(AUDIO_DIR / f"bed_{track}.wav")
    else:
        # format id -> themed real SMW bed (Stage 2: distinct beds per show)
        themed = {
            "news": "real_smw_title", "morning": "real_smw_overworld",
            "talk": "real_smw_overworld", "game_show": "real_smw_level",
            "late_night": "real_smw_castle", "action": "real_smw_level",
            "cartoon": "real_smw_overworld", "sitcom": "real_smw_overworld",
            "weather": "real_smw_title", "sports": "real_smw_level",
            "soap": "real_smw_title", "infomercial": "real_smw_castle",
            "rerun": "real_smw_overworld", "psa": "real_smw_title",
        }
        key = themed.get(track)
        if key:
            out.append(AUDIO_DIR / f"{key}.wav")
    return out


# --- real SPC capture hook (honest path) ------------------------------------
def capture_spc_via_emulator(rom: Path, out_spc: Path, retroarch: str = "",
                             bed: str = "real_smw_title") -> Optional[Path]:
    """Interface for the REAL audio route (per RESEARCH_SNES sec 4/6).

    Two modes:
      * Full SPC round-trip: run the ROM under snes9x/RetroArch, save an SPC
        (must be exactly 65,536 bytes), then render SPC->WAV with a *real* SPC
        player (spc-play / snes_spc / SNES_Sound_Utilities / pybrr). ffmpeg does
        NOT decode SPC. Returns the rendered WAV path.
      * Honest fallback (used when no SPC player is on PATH): returns the
        pre-staged emulator-captured bed WAV (method:"emulator_capture" from
        the snes9x DSP directly), so the broadcast still hears real SNES music
        even when the .spc round-trip toolchain is unavailable.

    It never fabricates a WAV. If neither a real SPC player nor a staged real
    bed exists, it returns None (recordered honestly, never a fake file).
    """
    # 1) Full SPC round-trip when a real player is present.
    player = _find_spc_player()
    if player is not None and rom.exists() and out_spc.exists() \
            and out_spc.stat().st_size == 65536:
        return _render_spc_to_wav(player, out_spc)

    # 2) Honest fallback: return the staged real emulator bed (real DSP audio).
    # This is real SNES music captured by the emulator, not a fake .wav.
    staged = AUDIO_DIR / f"{bed}.wav"
    if staged.exists():
        return staged
    # 3) Nothing honest available.
    return None


def _find_spc_player() -> Optional[Path]:
    """Locate a real SPC->WAV renderer on PATH, else None. This machine ships
    with no SPC player installed (verified 2026-08); if one appears later the
    full .spc round-trip activates automatically."""
    import shutil
    for exe in ("spc-play", "spc2wav", "pybrr"):
        p = shutil.which(exe)
        if p:
            return Path(p)
    return None


def _render_spc_to_wav(player: Path, spc: Path) -> Optional[Path]:
    """Render an SPC file to WAV with the given SPC player. Shape: real SPC in
    -> 44.1k stereo WAV out. Returns the WAV path or None on failure."""
    import subprocess, tempfile
    out = AUDIO_DIR / f"real_{spc.stem}.wav"
    try:
        if player.name == "pybrr":
            subprocess.run(["python", "-m", "pybrr.spc", "-o", str(out), str(spc)],
                           check=True, timeout=120)
        else:  # spc-play / spc2wav accept `spc -o out.wav`
            cmds = [[str(player), str(spc), "-o", str(out)],
                    [str(player), "-o", str(out), str(spc)]]
            ok = False
            for c in cmds:
                try:
                    subprocess.run(c, check=True, timeout=120)
                    ok = out.exists()
                    if ok:
                        break
                except Exception:
                    continue
            if not ok:
                return None
        return out if out.exists() else None
    except Exception:
        return None


def load_audio(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32767.0
    return data


class Mixer:
    """Provides an audio track for the ffmpeg mux, keyed by segment."""

    def __init__(self):
        self._cache: dict[str, np.ndarray] = {}

    def track_for(self, fmt: str, seconds: float):
        key = f"{fmt}:{int(seconds)}"
        if key in self._cache:
            return self._cache[key]
        bed = ensure_bed(fmt, min(seconds, 12.0))
        data = load_audio(bed)
        if len(data) < int(seconds * RATE):
            reps = int(np.ceil(int(seconds * RATE) / len(data))) + 1
            data = np.tile(data, reps)
        self._cache[key] = data[: int(seconds * RATE)]
        return self._cache[key]


mixer = Mixer()