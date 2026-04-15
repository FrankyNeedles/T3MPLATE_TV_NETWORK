#!/usr/bin/env python3
"""
ROM Audio Extractor
Extracts SPC700 sequences and BRR samples from SNES ROMs.
Enhanced with BRR decode.
"""

import logging
from pathlib import Path
import struct
import wave

logger = logging.getLogger(__name__)


class ROMAudioExtractor:
    def __init__(self, rom_path: Path):
        self.rom_path = rom_path
        self.rom_data = self._load_rom()

    def _load_rom(self) -> bytes:
        logger.info(f"Loading ROM from {self.rom_path}")
        with open(self.rom_path, "rb") as f:
            data = f.read()
        logger.info(f"ROM loaded: {len(data)} bytes")
        return data

    def _brr_decode(self, raw_brr: bytes) -> list[int]:
        """Basic BRR decoder (snes9x-inspired stub)."""
        samples = []
        i = 0
        last = 0
        while i + 1 < len(raw_brr):
            header = raw_brr[i]
            i += 1
            if header & 0x01:
                break
            range_v = (header >> 4) & 0x0F
            if range_v == 0x0F:
                continue
            scale = 1 << (range_v + 8)
            for j in range(4):
                if i >= len(raw_brr):
                    break
                nibble_byte = raw_brr[i]
                nibble = (nibble_byte >> 4) & 0x0F if j % 2 == 0 else nibble_byte & 0x0F
                delta = ((nibble & 0x0F) - 8) * scale // 16
                sample = min(max(last + delta, -32768), 32767)
                samples.append(sample)
                last = sample
                if j % 2 == 1:
                    i += 1
                if len(samples) > 32000:
                    break
            if len(samples) > 32000:
                break
        return samples[:32000]

    def extract_brr_samples(self, offsets: dict) -> dict:
        """Extract BRR samples and decode to WAV (enhanced)."""
        samples = {}
        audio_dir = Path("assets/audio")
        audio_dir.mkdir(exist_ok=True, parents=True)
        for name, offset in offsets.items():
            addr = int(offset, 16)
            raw_size = 1024  # Example for multiple blocks
            raw_brr = self.rom_data[addr : addr + raw_size]
            pcm = self._brr_decode(raw_brr)
            if pcm:
                wav_path = audio_dir / f"{name}.wav"
                with wave.open(str(wav_path), "wb") as f:
                    f.setnchannels(1)
                    f.setsampwidth(2)
                    f.setframerate(32000)
                    f.writeframes(b"".join(struct.pack("<h", p) for p in pcm))
                samples[name] = {
                    "raw_length": len(raw_brr),
                    "pcm_length": len(pcm),
                    "wav_path": str(wav_path),
                }
            else:
                samples[name] = {"raw": raw_brr, "decoded_wav": None}
        return samples

    def extract_spc_sequence(self, spc_offset: int) -> bytes:
        """Dump SPC700 RAM/sequence (placeholder)."""
        # In full impl: Use snes_spc lib
        return b"SPC-SEQUENCE-DUMP"  # Placeholder


# Example usage
if __name__ == "__main__":
    extractor = ROMAudioExtractor(Path("roms/sample.sfc"))
    brr_samples = extractor.extract_brr_samples({"jump": "0x500"})
    print(f"Extracted {len(brr_samples)} BRR samples")
