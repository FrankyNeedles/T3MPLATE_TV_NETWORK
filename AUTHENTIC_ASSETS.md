# AUTHENTIC_ASSETS — the correct capture route (truth, not a fix-me trap)

Authentic SNES material is captured from a real emulator — never hand-rolled
from raw ROM bytes. The dead `app/` and `extractors/` stacks that tried static
ROM decoding (and produced noise / fake files) are GONE. Do not resurrect them.

**The one honest route (this project's proven path):**

1. **Emulator-capture the ROM's rendered output** (per `RESEARCH_SNES.md` /
   `references/snes-emulator-capture.md`):
   - **Visuals:** RetroArch (1.22.2 + `bsnes`/`snes9x` core) playing the real
     ROM; screenshot/record the *rendered* frames, then key out the backdrop.
     Curated sprite rips from a verified source are also acceptable — recorded
     in `assets/catalog.json` with an honest `method`.
   - **Audio:** snes9x **DSP audio via the built-in FFmpeg record** — the SPC700 /
     SPC-DSP renders the music, so you get real SNES sound without decoding
     BRR yourself. This is exactly how the shipped `real_smw_*.wav` beds were
     made (`method: "emulator_capture"`, see `assets/audio/manifest.json`).
   - Unmapped formats fall back to the honest `synth` chiptune bed
     (`tvn/audio.py`) — tagged `method:"synth"`, never passed off as ROM data.

2. **`*.sfc` files stay untracked** (`.gitignore` ignores `roms/`, `*.sfc`,
   `*.smc`, `assets/large/`). The 10-byte fake `assets/t3mplate_tv.sfc` is
   removed and not coming back.

**Rule (Substance-over-Slop):** no placeholder or hand-rolled renderer output
is ever labelled authentic. If a `tvn/` feature needs real SNES pixels or
audio, produce it via RetroArch DSP/screenshot capture, record the provenance
in `catalog.json` / `audio/manifest.json`, and let the `real_art` / `real_audio`
gates verify it before it reaches the broadcast.