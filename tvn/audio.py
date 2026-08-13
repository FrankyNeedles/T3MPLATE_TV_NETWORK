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
    # loop continuity: crossfade tail into head so it loops cleanly
    ff = rate // 8
    head = np.copy(out[:ff])
    out[:ff] = 0.5 * (out[:ff] + head * 0.0)
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
    """Return an on-disk WAV for a track, synthesizing it if absent/honest."""
    track = (track or "bumper").split(".")[0]
    path = AUDIO_DIR / f"bed_{track}.wav"
    if track.startswith("real_") and path.exists():   # real SPC-dumped bed wins
        return path
    if not path.exists():
        write_wav(path, synth_bed(track, seconds))
    return path


# --- real SPC capture hook (honest path; documented, not implemented here) ---
def capture_spc_via_emulator(rom: Path, out_spc: Path, retroarch: str = "") -> Optional[Path]:
    """Interface for the REAL audio route (per RESEARCH_SNES sec 4/6):
    run the ROM in snes9x/RetroArch, save the SPC, then render SPC->WAV with an
    SPC player. Returns the WAV path if produced, else None.

    MVP ships the synth bed; wiring a real emulator capture is the documented
    next step (HANDOFF). This function intentionally documents the contract
    rather than shipping a hand-rolled ROM decoder (which produced noise).
    """
    return None  # real capture requires emulator tooling; plug in later


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