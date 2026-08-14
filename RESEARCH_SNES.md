# RESEARCH_SNES — Authentic SNES Asset Extraction: A Honest, Reliable Recipe

**Audience:** The builder of T3MPLATE TV ("the SNES world as a living 90s network broadcast").
**Scope:** Read-only domain research. Nothing in this document modifies any project file.
**Goal:** Replace the failed "every pixel traceable to real ROM data" pipeline with a recipe that actually produces authentic assets, and explain exactly why the previous one produced noise.

---

## 0. TL;DR — Why the old pipeline failed (proven, from the actual code)

I read `extractors/snes_rom_hacker.py`, `authentic_snes_extractor.py`, `world_asset_extractor.py`, `all_rom_extractor.py`, `rom_audio_extractor.py`, the catalog, the manifests, and the output files. The failure is not an implementation bug — it is a **category error about where data lives on a SNES**. Every one of these is false:

| Old assumption | Reality | Consequence |
|---|---|---|
| "CGRAM palette at ROM address `0x21200`" | `0x21200` is a **hardware register** (`$2122` CGDATA write port), not a ROM offset. CGRAM is **write-only** hardware RAM; palettes are never stored in ROM as a contiguous 512-byte dump. They live **per-game, often compressed, at game-specific offsets**. | Palettes were arbitrary ROM bytes → wrong colors on everything. |
| "SMW tilemap at ROM offset `0x3D800`" | `0x3D800` is a **runtime work-RAM address** (`$7E:3D800`, the current screen's 16x16 Map16 buffer), populated by the game at run time. It is **not** a static ROM offset. | The code ran `snes_to_offset(0x3D800)` and decoded arbitrary ROM code/data as a tilemap → garbage backgrounds. |
| "Extract sprite at `bank*0x8000 + offset`" across any ROM | Sprite/VRAM tile data is not at predictable offsets; each game packs VRAM differently, often compressed, and `bank*0x8000` is not even the correct LoROM/HiROM linearization. | Random pixel noise, broken templates — exactly what Frank saw. |
| "BRR audio at `0x100000` / `0x1DF380`" for any game | BRR samples are at game-specific locations referenced by each game's sound driver; you cannot guess. | 72–156-byte WAVs of silence/garbage (`feff faff` noise, all-zeros). |
| ADSR `attack:10, decay:10, sustain:80` | Hardcoded fake; not read from any ROM. | — |

**Smoking guns I confirmed on disk:**
- `assets/t3mplate_tv.sfc` is **10 bytes**: the ASCII text `TVSFC001\r\n`. It is *not a ROM at all* — it's a marker file. So the "asset foundation" ran against a non-ROM.
- `assets/audio/super_mario_world_theme.spc` is **4096 bytes**. A real SPC file is **65,536 bytes** (`0x10000`), starting with the text header `"SNES-SPC700 Sound File Data"`. This is a BRR/RAM fragment mislabeled as SPC.
- The catalog decodes `mario_0xd_0xac000` (bank `0xD`, offset `0xAC000`) as a 32×32 sprite. Real SMW Mario's GFX are *not* there; even if they were, a single 8-tile strip is not a usable character sheet.
- `authentic_snes_extractor.py` is **one line with literal `&#10;` newline entities** — the file is corrupted (HTML-escaped) and could not have run as-is.
- `.smc` files carry a 512-byte copier header that was never stripped, shifting every offset in manifest processing.

**The one correct thing:** header parsing (title/map mode/region/checksum) is structurally right — that part works and is genuinely reliable.

> **Core lesson:** On a SNES, graphics and audio are not at predictable file offsets. They live behind per-game decompression routines, in runtime VRAM/CGRAM, and in the SPC700's own RAM. You cannot write ONE generic "read 32KB here and decode" script that works across 784 arbitrary ROMs. That exact approach *is* the noise generator. Authentic extraction is **per-game**, or it is done at **runtime via an emulator**, not statically across a whole library.

---

## 1. SNES ROM Layout Fundamentals (LoROM / HiROM)

### The two memory mappings
A SNES CPU addresses the cart through 24-bit buses, but the CPU can only see **32KB at a time** via banks. Two dominant layouts:

- **LoROM** — each 64KB bank exposes only the **lower 32KB** (SNES `$8000–$FFFF` of each bank maps to ROM; `$0000–$7FFF` is WRAM/registers). ROM grows by 32KB per bank.
- **HiROM** — each bank exposes the **full 64KB** (SNES `$0000–$FFFF` maps to ROM). ROM grows by 64KB per bank.

Other, rarer: **ExHiROM** (0x40 banks), **SuperFX**, **SA-1**, **GSU** etc. — these use coprocessor memory maps. You'll hit them in a 784-ROM library (Starfox = SuperFX, Super Mario RPG = SA-1); treat those separately.

### File offsets → real data
A SNES address is `0xBBAAAA` (bank `BB`, low 16 bits `AAAA`).

```
LoROM: file_offset = (bank & 0x7F) * 0x8000 + (addr & 0x7FFF)
HiROM: file_offset = (bank & 0x3F) * 0x10000 + (addr & 0xFFFF)
```

**Copier header:** `.smc` files usually prepend **512 bytes** (a copier header: 0x10 bytes id + 0x1E0 zeros + 0x20 title/size block). **Strip it** before any offset math: `rom = data[512:]`. `.sfc`/`.fig` files are usually headerless. The old manifest never stripped this → every `.smc` offset was wrong.

### The header (it's at the END of the cart, not the start)
The header block is the **last 0x40 bytes of the ROM image**, always at SNES `$00FFC0`:
- **LoROM:** file offset `0x7FC0` (after stripping copier header).
- **HiROM:** file offset `0xFFC0`.

Byte map of the header (all offsets relative to the block start):

| Off | Len | Meaning |
|---|---|---|
| 0x00 | 21 | **Title** (ASCII, space/0x00 padded) |
| 0x15 | 1 | **Map mode** + ROM speed: `0x20/0x21/0x23`=LoROM, `0x30/0x31/0x35`=HiROM, high bits=ExHiROM/fast-rom |
| 0x16 | 1 | ROM type / coprocessor (0x05=SuperFX, 0x14-0x15=SA-1, 0x23=GSU, etc.) |
| 0x17 | 1 | **ROM size** = `0x400 << n` bytes |
| 0x18 | 1 | SRAM size = `0x400 << n` bytes |
| 0x19 | 1 | **Country/region code** (0x00=Japan, 0x01=USA, 0x02=Europe, 0x04=0x05=... full table exists) |
| 0x1A | 1 | Licensee code |
| 0x1B | 1 | Version |
| 0x1C | 2 | **Checksum complement** |
| 0x1E | 2 | **Checksum** (correct if `checksum + complement == 0xFFFF`) |
| 0x20 | 2 | **Native vector table** (reset vector at 0x20–0x21) |
| 0x24 | 2 | **Emulation vector table** |

**Why header parsing is the reliable win:** it is standardized and present in every legit ROM. It is the *only* thing you can correctly and uniformly extract from all 784 ROMs with zero per-game knowledge. Everything else is harder.

**Detection heuristic (don't trust a single address):** parse both candidate offsets (0x7FC0 and 0xFFC0) after stripping copier header, validate the checksum complement `== 0xFFFF` (or CRC of the whole image), and prefer whichever header's checksum passes. The old code's "try 0x7FDE then 0xFFDE, fallback to size" is reasonable — keep it, but add copier-header stripping and validate against both.

---

## 2. Tilemaps (BG graphics)

### The 4bpp tile (the atomic graphics unit)
Every SNES tile is **8×8 pixels**. The most common format is **4 bits-per-pixel (4bpp)** = 4 color bits per pixel = 16-color tiles:

- **32 bytes per 8×8 tile** (4 planes × 8 bytes).
- Each plane is 8 bytes, one byte per row, **MSB-first** (bit 7 = leftmost pixel).
- Pixel `(x,y)` value = 4-bit index: `bit0` from plane0, `bit1` from plane1, `bit2` from plane2, `bit3` from plane3 (i.e., assemble the bits, low bit = plane0).
- The 4-bit index selects a color from a **16-entry palette** (of 8 possible sub-palettes in CGRAM). Index `0` is usually transparent for sprites.

Also seen: **2bpp** (16 bytes/tile, 2 planes — text/SMS-style, some games), **8bpp** (64 bytes/tile, 8 planes — SMW's title, some BG).

### The tilemap entry (how the map references tiles)
A BG tilemap (the SNES "BG character map" in VRAM) is a grid of 2-byte entries. Standard format:

```
bit 15 : Y flip
bit 14 : X flip
bit 13 : priority (above/below sprite layer)
bit 12-10 : palette number (0-7), selects the 16-color sub-palette
bit 9-0  : tile number (index into the BG tile VRAM)
```

A 32×32 tilemap = 1024 entries × 2 bytes = **2048 bytes**. The tile number indexes into the VRAM tile region; the SNES renders `tile = VRAM[base + tile_number * 32]`.

### map16 / map32 (the metatile concept)
Games rarely store 8×8 directly in a level. **SMW (and many platformers) store levels as Map16 metatiles — 16×16 blocks made of four 8×8 tiles, plus a table of which 8×8 tiles they're made of.** (Map32 = 32×32 metatiles, used by SMW's overworld.) So the pipeline is:

```
ROM level data (compressed, custom format)
  → decompress → Map16 ID grid (16×16 metatiles)
  → Map16 definition table (maps each ID → 4 tile indices + tile attrs)
  → 8×8 tile data (GFX, often compressed, separate from the level)
  → VRAM
```

This is why "read the level tilemap at `0x3D800`" is wrong for a ROM file: **the Map16 buffer at `$7E:3D800` is built at runtime** by SMW's level-loading routine from the compressed level data. There is no static ROM array there to read.

### How to ACTUALLY get a background tilemap (honest options)
1. **Runtime dump (most reliable, generic):** Run the game in an accurate emulator (bsnes), pause at a screen, dump the BG tilemap + BG tile VRAM + CGRAM from the emulator's debugger/memory view. You get the *exact* rendered layer. This is authentic and works for any game.
2. **Level editor export (SMW):** Lunar Magic can export/import graphics and lets you view the Map16 data directly. For SMW specifically, this is the fastest correct path.
3. **Static (hard, per-game):** Disassemble the level-load routine to find the compressed level pointer table, then write the game's specific decompressor. Only worthwhile for a handful of flagship games you care about.

---

## 3. Sprites & Character Graphics

### Where sprite graphics live
Sprites (the OAM-driven moving objects) get their pixels from **VRAM tile data** at a tile number set per-sprite in OAM, and their colors from a **CGRAM sub-palette** selected by the sprite's palette bits. To render a real sprite you need **both**:
- the correct **8×8 or 16×16 tile bytes** (the game loads these into VRAM at run time from its own GFX, usually compressed), and
- the correct **16-color CGRAM sub-palette** the sprite uses.

### 16×16 tiles
Some games use 16×16 tiles for sprites (one OAM entry covers 16×16 = four 8×8 tiles, arranged with a specific order, sometimes a "checkerboard" layout with the two 8×8 halves swapped). 16×16 sprites require you to know the tile order and whether X/Y-flip is applied per 8×8 quadrant. Don't assume — check per game.

### 4bpp planar decode (exact)
For an 8×8 tile at a given offset, `data[0:32]`:
```
planes = [data[0:8], data[8:16], data[16:24], data[24:32]]
for row in 0..7:
    for col in 0..7:
        pixel = ((planes[0][row] >> (7-col)) & 1)
              | ((planes[1][row] >> (7-col)) & 1) << 1
              | ((planes[2][row] >> (7-col)) & 1) << 2
              | ((planes[3][row] >> (7-col)) & 1) << 3
```
This part of the old code (`extract_sprite`) was **correct**. The failure was the *address*, the *palette source*, and the *tile ordering*, not the bit unpacking.

### CGRAM palette structure (15-bit BGR555)
CGRAM holds **256 colors × 2 bytes** = 512 bytes. Each color word:
```
bits 0-4   : Red   (0-31)
bits 5-9   : Green (0-31)
bits 10-14 : Blue  (0-31)
bit  15    : unused
```
Note the bit order: the value is stored with **blue in the high field** (`BGR`). To convert to 8-bit RGB:
```
R8 = (color & 0x001F) << 3        # or * 255/31
G8 = ((color >> 5) & 0x001F) << 3
B8 = ((color >> 10) & 0x001F) << 3
```
**BUT:** as established, you cannot read "the CGRAM" from the ROM at a fixed address — it's write-only hardware RAM. To get a real palette you must:
- **Runtime:** dump CGRAM in an emulator when the sprite is on screen, or
- **Per-game offset table:** known documented CGRAM-load addresses (e.g. TCRF, romhacking.net docs) pointing at the ROM data the game *will* copy into CGRAM.

### Producing a real usable sprite sheet + .pal/.bin
Recipe that yields authentic output:
1. Pick a specific game + specific character/frame (e.g. SMW Mario idle).
2. Get the GFX tile offset (runtime dump or documented) → decode 4bpp tiles → assemble the animation frames into a **sprite sheet** (grid, consistent tile size, with per-tile attributes recorded: palette, flip).
3. Get the sprite's CGRAM sub-palette (runtime dump or documented load address) → write a standard **`.pal`** (the 512-byte raw CGRAM dump, or a JASC-PAL text file) and a **`.bin`** (raw tile data) alongside.
4. Record provenance: `{game, rom_sha256, bank, address, palette_source, frames}`.

> Real sprite ripping for arbitrary games is **manual, per-game work**. Tools like **YY-CHR** (tile editor, shows VRAM tiles + lets you apply palettes) and game-specific sprite sheets on **Spriters Resource** (for reference of correct appearance) exist precisely because this is game-specific. Do not attempt a generic auto-ripper across 784 ROMs — it will reproduce the exact noise problem.

---

## 4. Audio: SPC700 / S-DSP / BRR

### The audio subsystem
The SNES has a dedicated audio CPU:
- **SPC700** (8-bit CPU) runs the game's music engine.
- **S-DSP** synthesizes output; it plays **BRR-encoded samples** through **8 voices**, applying **pitch, ADSR envelopes, echo/filters**.
- The SPC700's **64KB of its own RAM** holds: the music engine code, the song data, and the **BRR sample data** that S-DSP reads directly.

### BRR format (bit-rate reduction — the sample codec)
BRR is an ADPCM-like codec. Samples are stored as **9-byte blocks**, each producing **16 samples**:

```
byte 0 (header):
  bits 7-4 : range (shift, 0-12)
  bit  3   : end flag (1 = last block of the sample)
  bits 2-1 : filter (0-3)
  bit  0   : loop flag (reserved; loop points are handled by the engine)
bytes 1-8 : 16 nibbles (4-bit deltas), packed MSB-first
```

Decode with **filter prediction** (each filter predicts the next sample from previous outputs):
- **Filter 0:** `out = delta`
- **Filter 1:** `out = delta + p1 - (p1 >> 4)`   (≈ 15/16 of previous)
- **Filter 2:** `out = delta + p1 - (p1 >> 4) + (p1 >> 3) - (p2 >> 6)`
- **Filter 3:** `out = delta + p1 - (p1 >> 4) + (p1 >> 3) - (p2 >> 4) + (p2 >> 3) - (p3 >> 6)`

where `delta` is the sign-extended 4-bit nibble shifted left by `range`, and `p1,p2,p3` are previous outputs. (Use a proven reference decoder — snes9x's `SPC_DSP` or the `brr` decoder in `spc-play`/`pybrr` — rather than hand-deriving coefficients. The old code's filter table is roughly right but a faithful reference is safer.)

### The SPC file format (the reliable extraction target)
An **SPC file is a frozen snapshot of the SPC700**, 65,536 bytes:
```
bytes 0x0000-0x00FF : ASCII header "SNES-SPC700 Sound File Data v0.30" + fields
                     (PC, A, X, Y, PSW, SP registers; timer/ADSR/echo params)
bytes 0x0100-0xFF3F : SPC700 RAM (64KB - 256 - extra)  → holds engine + BRR samples
bytes 0xFF40-0xFFBF : S-DSP register block (128 bytes)  → current ADSR/echo/voice state
bytes 0xFFC0-0xFFFF : extra RAM (often 0)
```
**A valid SPC must be 65,536 bytes.** The old project's 4096-byte `.spc` is not an SPC.

### How to actually get real music/SFX out of a SNES ROM — the ONE reliable way
Because every game's music engine is different, **you do not statically parse ROMs for audio**. You let the game play, then **freeze the SPC700**:

1. **Load the ROM in a SNES emulator with SPC-export** (snes9x standalone, or RetroArch's snes9x core with "Save SPC" / `spc` capture). Standalone **snes9x** has a "Save SPC" feature (and a debugger) that dumps the current music engine + samples to a `.spc` file.
2. **Play the track** you want (intro theme, level music, SFX).
3. **Trigger the SPC save** → you get a valid 64KB `.spc`.
4. **Render the SPC to audio** with an SPC player: `spc-play`/`SNES_Sound_Utilities` (`snes_spc`), `audio/ssemu`'s spc converter, or Python bindings. Output WAV/MP3.
5. For **BRR SFX specifically**, decode the BRR blocks already present in SPC RAM (the samples S-DSP uses), or render the SPC around the SFX moment.

**ADSR:** you don't need to extract ADSR at all if you render the SPC — the S-DSP register block in the SPC contains the real ADSR/echo state for every voice, and the player applies it. (The old code's hardcoded `attack:10,decay:10,sustain:80` was fabricated; discard it.)

This method is **100% authentic, zero reverse-engineering, per-game, and works across the whole 784-ROM library** with a scripted emulator. It is the single highest-value reliable extraction in this entire project.

---

## 5. Compression & Formatting — when raw vs decompress

### The hard truth
Almost no game stores graphics/levels/audio as raw bytes at predictable offsets. There is **no universal SNES compression** — each game uses its own, and often multiple:

- **SMW** uses:
  - **LC_LZ1** ("SMW compression") for most GFX: a 9-bit-LZ-style format with 16-byte literal/verbatim runs, used to compress 4bpp tile graphics.
  - **LC_LZ2** for some data.
  - Level data uses its own Map16/object encoding (not raw).
  - A **pointer table** near the top of each 0x8000-byte data bank (`$xx8000` for GFX) lists the offset of each compressed object within the bank.
- **Donkey Kong Country** uses its own **LZ-style** plus a proprietary pattern-matching packer.
- **Mega Man X series** use their own graphics compression.
- **Final Fantasy / RPGs** use bank-based pointers and custom tilemap encodings.

### The decision rule
- **Safe to read raw:** the ROM header (section 1), and any *documented* raw tables. Nothing else is safe by default.
- **Must decompress / must go through the game:** tile data, tilemaps, level maps, sprites, palettes (usually compressed or loaded from tables), BRR samples (their *location* is engine-driven even though the samples themselves are raw once found).

### Pointer tables (the key to finding things)
Games commonly keep a **pointer table**: a contiguous array of 16-bit (or 24-bit bank+offset) values, each pointing at a compressed/raw chunk. To find a specific asset you must:
1. Locate the game's pointer table (documented, or found by scanning for a sequence of pointers that resolve to in-bounds, plausibly-sized data),
2. Follow the pointer,
3. Apply the game's decompressor.

This is **per-game reverse engineering**. It is not something to automate blindly across 784 ROMs.

---

## 6. PRACTICAL, HONEST PIPELINE — the minimal reliable path

Given a 784-ROM library, here is what actually works, ordered by reliability-to-effort. The goal: authentic assets (backgrounds, a few characters, BRR audio) without re-running the noise generator.

### Tier 1 — Do this first (reliable, cheap, 100% authentic)
1. **ROM metadata for all 784 ROMs.** Fix the existing manifest builder:
   - **Strip the 512-byte copier header** from `.smc` files.
   - Parse header at the *end* of the image (0x7FC0 LoROM / 0xFFC0 HiROM), validate checksum complement, emit `{title, region, map_mode, coprocessor, size, sha256}`.
   - This is the only "every pixel traceable" backbone you can honestly produce at scale. Use it to pick WHICH games to extract real assets from.

2. **Real music/SFX for every game via SPC capture (the killer feature).**
   - Script a headless snes9x (or RetroArch snes9x core) that: loads each ROM → boots to title/intro → triggers SPC save → quits.
   - Collect valid 64KB `.spc` files per game.
   - Batch-render with an SPC player to `.wav`/`.mp3` (and optionally decode in-sample BRR to separate SFX).
   - This gives you **authentic theme music + SFX for dozens of games** with no per-game reverse engineering. It is exactly what a "living 90s TV station" needs for its audio bed, bumpers, and jingles.

### Tier 2 — Do this next (a curated authentic visual kit)
3. **Pick ~5–10 flagship games** (SMW, DKC, Zelda: LTTP, Mega Man X, EarthBound, Starfox, Kirby, Final Fantasy VI, Chrono Trigger, Super Metroid) — games whose internals are heavily documented.
4. **Backgrounds:** For each flagship, dump the BG tilemap + BG VRAM + CGRAM at runtime from an accurate emulator (bsnes) at representative screens; or use documented offsets + the game's specific decompressor. Produce genuine backgrounds with provenance.
5. **A few characters:** For each flagship, runtime-dump the character's GFX tile block + the sprite's CGRAM sub-palette; assemble into a proper sprite sheet + `.pal` + `.bin`, with `{game, sha256, address, palette_source, frames}` recorded. ~8–16 characters total is plenty for a TV network's cast.

### Tier 3 — Automate the *metadata* only, never the graphics
6. Auto-scan the whole library for header metadata and (optionally) for *presence* of audio/GFX markers, but **do not** attempt generic sprite/BRR extraction across all ROMs. That is the trap that produced the noise.

### What to avoid (the exact failure modes)
- ❌ Reading bytes at guessed offsets (`bank*0x8000 + guess`) and decoding as 4bpp/BRR. **This is the noise generator.** Delete that pattern.
- ❌ Treating hardware register addresses (`0x21200` CGRAM, `0x3D800`) as ROM offsets.
- ❌ Writing `.spc` that isn't 65,536 bytes, or WAVs that are 72 bytes of `feff faff`.
- ❌ Fake ADSR / fake palettes / hardcoded sprite sizes without a real source.
- ❌ Forgetting copier headers on `.smc`.
- ❌ Building "assets" from `t3mplate_tv.sfc` — it is a 10-byte marker, not a ROM.

### Concrete stack (Python-friendly)
- **Header/offsets:** implement copier-header strip + LoROM/HiROM linearization yourself (20 lines, section 1); `snes_reader` / `snesutils` can help.
- **Emulation + dumping:** **snes9x** (SPC export, debugger) and **bsnes** (accurate VRAM/CGRAM/tilemap dump). RetroArch with the `snes9x`/`bsnes` cores for scripting.
- **SPC render/BRR decode:** `snes_spc` / `spc-play` / `SNES_Sound_Utilities`; Python: `snes_spc` bindings, `pybrr`, `spc2wav`.
- **Tiles/sprites:** **Pillow** (already used), **numpy** for batched tile unpacking; **YY-CHR** for manual/visual tile work.
- **Game-specific:** **Lunar Magic** (SMW: Map16, GFX export), romhacking.net + TCRF docs for per-game offsets and formats.
- **Sanity tooling:** add a validator that rejects assets failing the "authentic" bar (SPC ≠ 64KB → reject; sprite with no palette source → reject; WAV < ~1KB or pure silence → reject; no sha256 provenance → reject). The old `validate_assets.py` only checked *offset formats*, not *data plausibility* — that's why noise passed.

---

## 7. Assessment of the old pipeline (recap with evidence)

- **Correct:** header parsing logic, the 4bpp tile bit-unpacking, the manifest/hash provenance *concept*, the BRR block size constant (9), the 15-bit BGR555 palette math.
- **Broken/illusory:** every offset was guessed or a hardware register; no copier-header handling; `.spc` not real; ADSR fabricated; `t3mplate_tv.sfc` is not a ROM; `authentic_snes_extractor.py` is corrupted (literal `&#10;` entities); validator checked offset strings, not data.
- **Root cause:** generic static extraction across arbitrary ROMs is impossible on SNES. The project conflated "can decode the format" with "knows where the data is." The format decoding was fine; the data location was invented.

---

## 8. BEST NEXT ACTION (recommended)

**Immediately switch the asset backbone from "static offset decoding" to "runtime capture + curated per-game extraction," and prove it on ONE game end-to-end.**

Concretely, in order:
1. **Fix the manifest (30 min):** strip copier headers, parse end-of-ROM headers, validate checksums → a trustworthy 784-ROM catalog with provenance. This is the honest "traceable" layer.
2. **Prove the audio path (the highest-value, cheapest win):** script snes9x to auto-capture SPC from **Super Mario World** (and one or two others) → render to WAV → ship authentic theme + jump/coin SFX as your first verified assets. This immediately replaces the 72-byte noise files with real audio.
3. **Prove the visual path on SMW only:** use Lunar Magic / a runtime VRAM+CGRAM dump to produce (a) one authentic background (e.g. overworld or a castle) and (b) the Mario sprite sheet + `.pal`. That becomes the template, with full provenance.
4. **Then scale metadata across the 784** and hand-pick ~10 flagship games to repeat step 3 for a curated cast/set kit — **never** a generic all-ROM auto-extractor.

If the builder wants, I can next (a) write the corrected header/copier-strip module, (b) script the snes9x SPC-capture batch, or (c) build the runtime VRAM/CGRAM dump recipe for SMW as a concrete reference implementation.
