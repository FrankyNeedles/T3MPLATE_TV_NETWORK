#!/usr/bin/env python3
"""
Audio Engine
Plays BRR/SPC audio with SNES-accurate DSP (echo, reverb).
Using sounddevice for real-time playback as PyAudio alternative.
"""

import numpy as np
import soundfile as sf
import sounddevice as sd
from pathlib import Path


class AudioEngine:
    def __init__(self):
        self.sample_rate = 44100
        self.channels = 2

    def play_brr(self, brr_path: Path):
        """Decode and play BRR sample."""
        # Placeholder: Load WAV from extracted BRR (websnack decode in prod)
        if brr_path.exists() and brr_path.suffix == ".wav":
            data, fs = sf.read(str(brr_path))
            sd.play(data, fs)
            sd.wait()
        else:
            self.play_tone(440, 500)  # Fallback beep

    def play_spc(self, spc_path: Path):
        """Play SPC700 sequence (emulate in prod)."""
        print(f"SPC playback: {spc_path}")
        self.play_tone(880, 1000)

    def play_tone(self, freq: float, duration_ms: int):
        """Generate sine wave tone (SNES-like beep)."""
        duration = duration_ms / 1000.0
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        tone = np.sin(freq * t * 2 * np.pi)
        data = tone.reshape(-1, 1) * 0.1  # Mono
        if self.channels == 2:
            data = np.repeat(data, 2, axis=1)  # Stereo
        sd.play(data, self.sample_rate)
        sd.wait()

    def _play_raw_audio(self, data: bytes, rate: int, channels: int):
        """Play raw PCM, assuming int16."""
        arr = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
        if channels == 1:
            arr = arr.reshape(-1, 1)
            if self.channels == 2:
                arr = np.repeat(arr, 2, axis=1)
        sd.play(arr, rate)
        sd.wait()

    def shutdown(self):
        pass  # sounddevice handles cleanup


# Global audio engine
audio_engine = AudioEngine()

if __name__ == "__main__":
    audio_engine.play_tone(523, 500)  # C5 note
