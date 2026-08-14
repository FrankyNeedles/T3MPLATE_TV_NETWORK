# RESEARCH_ASSETS.md — Substance-over-Slop Quality Gate Blueprint

**Scope:** Asset pipeline engineering for the SNES-world-as-living-90s-TV broadcast (T3MPLATE TV WORLD).
**Purpose:** This is the QUALITY GATE contract between **authentic extraction** (real ROM-derived assets) and a **watchable broadcast**. It defines, concretely and mechanically, how to guarantee "every pixel traceable" and how to make it impossible for noise to ever reach the screen.
**Status:** RESEARCH ONLY (read-only assessment). No project files were modified. This document is the blueprint the builder implements against.

---

## 0. Why the old pipeline produced "slop" — root-cause diagnosis (grounded in the code)

Before defining the fix, the failure modes must be named precisely. Each maps to a real file in `extractors/`:

**R1. Guessed addresses applied blindly across all ROMs** — `all_rom_extractor.py` extracts the "same common sprite" from *every* ROM at a hardcoded address (`extract_sprite(0x028000, (32,32))`, bank 2 / offset 0x8000), a hardcoded "typical BRR area" (`decode_brr_stream(..., 0x100000)`), and a hardcoded SMW BG tilemap address (`0x3D800`) applied to non-SMW games. The on-disk sprite artifacts confirm it: filenames like `megaman_0x1_0x80000.png`, `mario_0xd_0xac000.png`, `diddy_0x2_0x82000.png` — offsets clustered on round boundaries (0x80000, 0x82000, 0x84000, 0x86000, 0x8a000, 0xac000…) are *scan heuristics*, not pointer-chased real sprite locations. Reading 32×32 bytes at a near-arbitrary ROM address and coloring them yields **random pixelated sprites** by construction.

**R2. CGRAM "palette extraction" reads the wrong thing** — `extract_cgram(0x21200)` and the `SMW_CGRAM_ADDR = 0x21200` constant treat the CGRAM **hardware register address** as if it were ROM data. `$21200` is an MMIO register; the live palette lives in CGRAM **RAM during runtime**, it is not a static blob in the ROM file. Reading ROM bytes at the mapped offset returns arbitrary code bytes, not a palette. Result: every sprite is colored with a **fabricated palette** → wrong/random colors regardless of how correct the tile decode is.

**R3. Offset "validation" checks metadata, never content** — `validate_assets.py` only asserts an offset string starts with `0x` or happens to appear on a scraped TCRF page. It never inspects the produced image/audio. So `valid == total` (e.g. "422/422 valid") is achievable while **every sprite is pixel garbage**, every audio file is noise. This is the single most dangerous lie in the old pipeline: a green counter with zero perceptual authority. Many catalog entries carry `"verified": true` set heuristically (round-number offset + no exception), which blinded the project to the noise for months.

**R4. "Success" = an exception was not raised** — `world_asset_extractor.py` / `pipeline.py` mark `extracted: true` merely because `img.save()` succeeded. A file existing on disk is treated as a valid asset. No content gate, no dimension check, no palette check, no round-trip check.

**R5. Audio is decoded but never confirmed to sound like anything** — the BRR block decoder (`decode_brr_block`) is roughly correct, but it is fed bytes from guessed offsets; `decode_brr_stream` terminates on a zero header and otherwise decodes arbitrary ROM bytes. No check for nonzero RMS, loop continuity, duration, or musical structure. Output is silence or hash-noise and is shipped as "music."

**R6. No curate stage and no runtime guard** — nothing between "file written" and "rendered on the 90s TV." A broken template / mis-colored sprite / empty track still renders because the broadcast layer has no load-time validation.

**Net:** the pipeline produced noise because *nothing* in it was designed to reject noise. It validated *attempts*, not *artifacts*.

---

## 1. What "substance over slop" means concretely here

For this project the phrase stops being a slogan and becomes three countable properties every shipped asset must hold:

1. **Source-verifiable** — the asset is traceable to a specific byte range in a specific ROM, via a **real** address (pointer-chased or ROM-hacking-documented), with a cryptographic hash tying the extracted bytes to the source ROM's hash.
2. **Not random** — the asset passes deterministic content checks proving it is *structured signal* (real tiles, real palette entries, real looped audio), not entropy read off a wrong address (Section 4).
3. **Usable in context** — the asset renders meaningfully in a 90s broadcast: a sprite fits its framing/palette, a background lays out on a screen, audio loops without clicking. *Usable = it survives a live render smoke test*, not just a file-existence test.

**The quality bar (the single sentence):**
> An asset is ADMITTED to broadcast only when it is (a) cryptographically tied to a real ROM and a real extraction method, (b) deterministically proven to be structured content (not noise), and (c) integration-smoke-tested in the broadcast context — i.e. it survived **verify → curate → catalog → render**, every gate green.

**Honest validation gates (the contract):**
- **GATE = evidence, not opinion.** A "verified" claim must be reproducible by re-running the check. Never mark verified from a heuristic (round number, no-exception, filename).
- **Content gates are mandatory; metadata gates are necessary but never sufficient.** Offset-format checks may run first, but a green metadata check alone must NEVER set `verified`.
- **Fail loudly, not silently.** If an asset cannot pass a gate, it is quarantined to `assets/_quarantine/` with a `rejected` status and the reason recorded. It must not be "almost used."
- **Downgrade honesty** (per FULL_VISION §Pillar 1): any claim that later proves false (e.g. "ROM assets" that are actually guesses) is downgraded to `verified: false` and the asset is pulled from broadcast until re-validated.

---

## 2. Robust pipeline design: extract → verify → curate → catalog → render

Each stage has a single job and concrete checks that make the R1–R6 failures structurally impossible.

### STAGE A — EXTRACT (address discovery that is *real*, not guessed)
The root fix for R1/R2. An address is "real" only if obtained one of:
- **Pointer chase / tilemap walk:** read the BG tilemap / OAM table / GFX pointer table to locate the actual sprite/tile GFX, then run DMA-style decoding (2bpp/4bpp/8bpp planar). This is how an emulator finds graphics — replicate that.
- **ROM-hacking documented offsets:** a known, documented offset for that specific game (from TCRF *page text*, disassembly, or a per-game config), double-checked against a decoded result.
- **Structural search with validation:** scan for a *candidate* region and accept ONLY if the candidate decodes to structured tiles whose palette entries are actually referenced (Section 4). Never accept a candidate on the basis of position alone.

Concrete checks at extract time:
- [ ] The **SNES address is mapped to a ROM file offset** using the correct LoROM/HiROM mapping AND the header is parsed (do not use a fixed `0x21200`; do not assume a bank).
- [ ] **Palette source is the real CGRAM image for that sprite/tile** — obtained from an emulator memory dump, a documented CGRAM init routine (search code for writes to `$2121`/`$2122` to recover the palette), or a per-game palette table in the ROM — **never** an arbitrary ROM slice masquerading as CGRAM.
- [ ] Extract at the **format of the actual graphics** (2/4/8bpp planar tiles, tile dimensions, size per tile = bpp/2×8×8). Sprites are not "32×32 raw bytes."
- [ ] For audio: locate BRR via the SPC700's **sample directory** (indexed pointer table to BRR blocks, per DSP write to `$5D`), not "a typical BRR area."
- [ ] Record the **exact method** used (pointer-chase / documented-offset / structural-search) and the **exact SNES address + bank** in the provenance (Section 5).

### STAGE B — VERIFY (cryptographic + content; Section 4 is the detail)
- [ ] Re-derive the asset from the source bytes and confirm a **round-trip**: extract → decode → re-encode → compare to source (e.g. decode the tilemap, re-serialize, byte-equal; if not, the address/decode is wrong).
- [ ] Confirm the asset's bytes hash **matches the source ROM's hash + offset** fingerprint (no two different ROMs can produce the same asset claim).
- [ ] Run the **deterministic noise battery** (Section 4). Any failure → quarantine + `verified:false`.
- [ ] Zero assets are marked `verified:true` at this stage by metadata alone.

### STAGE C — CURATE (the human/LLM quality gate — the "looks intentional" pass)
This is where "not noise" becomes "looks intentional in a 90s broadcast." (Details in Section 3.) Concrete checks:
- [ ] **Sprite:** within the framing, alpha/transparency coverage is sane, bounding box is non-trivial, palette count is within a SNES-plausible range (≤ 15 colors on the 16-color subpalette + transparency), and the image is not a 1px column / full-frame fill / single-color slab.
- [ ] **Background:** tiles form a coherent composition (repeating tiles + distinct feature tiles, not 1024 random tile indices); palette references resolve to defined entries.
- [ ] **Audio:** loop points are set, duration is broadcast-plausible (a jingle is 3–15 s, not 0.1 s or 30 min of silence), no clipping after normalization.
- [ ] Decision is **recorded**: `status: curated|curated-with-notes|rejected`, with a one-line human/LLM rationale stored in the manifest. A green verify + a curate rejection is normal and correct.

### STAGE D — CATALOG (the manifest; Section 5 is the schema)
- [ ] Every admitted asset gets one immutable catalog record: `asset_id`, provenance (ROM, hash, address, method), content fingerprint (sha256 of the artifact), verify results, curation verdict, and `status`.
- [ ] Catalog is **append-only**: a rejected or downgraded record is never deleted, only `status`-updated — the audit trail is the promise of "every pixel traceable."
- [ ] The catalog is the **only** thing the broadcast layer may read. No direct path globbing for `*.png` in the broadcaster.

### STAGE E — RENDER (runtime guards so a broken asset can never draw)
- [ ] At broadcast startup, the renderer **loads every scheduled asset against its catalog record** and fails the slot (falls back to a test-pattern / color-bars / station-ID loop — the period-correct failure state) if any load-time check fails.
- [ ] Load-time checks per asset type (Section 4 "runtime guards"): correct dimensions, valid palette, non-empty alpha, non-silent audio with defined loop.
- [ ] A top-level **Red/Green gate**: broadcast refuses to start (or refuses the specific segment) while any *scheduled* asset is `status != ready`.
- [ ] Every rendered frame logs its asset + catalog `asset_id`, so a "bad frame" can be traced to its exact source bytes.

---

## 3. From AUTHENTIC to INTENTIONAL: making real assets LOOK like they belong on 90s TV

Authentic ≠ watchable. The ROM gives you raw tiles/samples; the *broadcast* needs composition. This section is the anti-"random garbage on screen" design rules.

### Sprite posing / framing
- **Extract the full animation frame set for a character, not one snapshot.** A pose is intentional when it has a background, a mid, and a foreground relationship. Pull idle/walk/talk/happy/angry frames from the game's real animation; pick poses by *dramatic intent* (news anchor = rest pose, game-show host = wave pose).
- **Framing contract:** every character sprite is placed on a consistent ground line and consistent scale relative to the set (a 16×16 sprite and a 48×48 sprite don't share a talk-show couch). Define per-show "cast scale" and normalize via SNES-native whole-pixel scaling only (no blurry nearest-neighbor upscale beyond what the hardware would do).
- **Composition rule:** character occupies the intended region; bounding box bottom sits on the set's ground line; sprite faces into the frame (don't have Mario staring at the screen edge). These are deterministic checks (bbox location, facing = most ink on one side), not vibes.

### Palette handling
- **Keep the palette as the source of truth.** A sprite is `authentic + intentional` when its pixels only reference colors that (a) exist in the real extracted subpalette and (b) are used in the actual render. Never post-process into arbitrary RGB — SNES colors are 15-bit; stay quantized to the real palette.
- **Cross-asset palette discipline:** two assets in the same broadcast frame must not fight (e.g. a Mario subpalette and a Zelda subpalette both rendering). If mixing, derive a **master broadcast palette** from the real palettes and remap *to it* deterministically at catalog time — the catalog records the remap so it's auditable.
- **Check:** every indexed pixel value must resolve to a defined palette entry; palette index 0 reserved as transparent where the sprite is not opaque; no color channel exceeds SNES 5-bit range after conversion.

### Background composition
- Real tilemaps are 32×32 tiles; a 90s set is 256×224. **Build the screen from real tiles** (forest tiles, castle tiles) rather than sampling random bytes. Compose: a "backdrop" layer (parallax sky/trees), a "set" layer (desk, floor, props) made of real tiles arranged on the real palette.
- **Coherence check:** tile usage histogram — a good background has a handful of heavily-repeated structural tiles + a set of unique feature tiles; a "slop" background is high entropy across all 1024 slots (Section 4 entropy check catches this).
- Layer the 90s TV treatment on top **after** composition (scanlines, chromatic aberration, vignette — per FULL_VISION §Technical Authenticity) so the treatment reads as *broadcast* and never as *broken capture*.

### Looping audio
- **Cyclic structure:** a jingle/theme must loop cleanly. Set the loop point to the real loop (BRR end-flag → start-of-loop) or a silent/beat-aligned splice. **Check:** crossfade-free loop must not click — assert that sample[loop_end-1] ≈ sample[loop_start] (or that a seamless fade is applied) and that RMS before/after loop is continuous.
- **Broadcast length discipline:** loop-able bed 15–40 s, jingle 3–12 s, SFX < 1 s. Anything outside is a symptom of a mis-extraction, not a stylistic choice.
- **Level discipline:** normalize beds to an average loudness target (-14 to -18 LUFS-ish amplitude, mean |x| in a sane band), clamp peaks below clipping. A track that never crosses a low RMS floor is probably silent/placeholder.

---

## 4. Validation framework — deterministic "is this noise?" checks + runtime guards

These must be run automatically, fail closed, and be reproducible. No ML judgment required at gate A/B — only at curation (which is optional/flagging, never the sole authority).

### 4.1 Sprite / image checks (`quality:image`)
- **Non-empty alpha:** fraction of non-transparent pixels in [0.02, 0.95]. A sprite that is full-frame opaque (a slab) or basically empty (1 px dot) is a broken extraction.
- **Bounding box:** bbox area / canvas ≥ 0.01 and ≤ 0.90; not a 1-pixel-wide column or row.
- **Used color count:** distinct non-transparent palette indices between 2 and 15 (a 16-color subpalette can't use more; 1 color = a solid rectangle = guess).
- **Structure / entropy:** compute the decoded tile-level entropy. Genuine sprite GFX shows repeating structure across the 8×8 tile grid (real tiles repeat); noise is near-maximal uniform entropy. Check: % of duplicate 8×8 tiles ≥ some floor (real sprites/cartoons compress), and within-tile edge density (Sobel magnitude) in a sane band — not ~0 (blank), not uniform saturation (noise/grain).
- **Round-trip integrity:** decode → re-encode → compare to source bytes; must match exactly.

### 4.2 Background checks (`quality:background`)
- **Tilemap reference validity:** every tile index resolves to a defined tile + palette entry (no out-of-range refs — this is the "broken sprite template" catcher).
- **Tile-use distribution:** normalize the 1024-tile histogram; entropy per tile < threshold (structured composition) and structural-tile coverage (top-N tiles account for ≥ 50% of slots) — real backgrounds repeat.
- **Dimension:** width×height is a valid broadcast map (e.g. 32×32 or 32×64 tiles → 256×256/256×512 px render), never degenerate 1×N.

### 4.3 Audio checks (`quality:audio`)
- **Non-silence:** peak level > -40 dBFS and RMS > -60 dBFS (rejects zero/empty tracks).
- **Loop integrity:** loop point defined; end-vs-start continuity (no >6 dB discontinuity / audible click).
- **Length band:** duration within per-type bounds (jingle 3–15 s, bed 15–40 s).
- **Energy over time:** spectral flatness / voiced presence — a "song" is not a single 4 kHz tone (that's usually noise or a misaligned read); require broad-ish spectral distribution and RMS variance over time (real music breathes).

### 4.4 Runtime guards (the broadcaster's load-time assertion layer)
Executed at load, per asset, before any draw/play; any failure → quarantine + fallback to color-bars/test-pattern for that slot:
```text
sprite:   size == catalog.size
          palette_refs all resolve (index < len(palette))
          alpha_coverage in [0.02, 0.95]
background: tilemap refs all in range; dims valid
audio:    peak > -40 dBFS; duration in type band; loop_set == true
```
Plus one **global guard**: broadcast refuses to start (or segment refuses to schedule) if its asset manifest contains any `status != ready` entry. Broken assets simply cannot render — the failure mode is a period-authentic "technical difficulties" / test pattern, never pixel garbage on screen.

---

## 5. Asset catalog schema — the manifest that makes the broadcast auditable

The catalog is the single source of truth the renderer reads. It is **append-only**, so every downgrade/rejection is preserved — that is what makes "every pixel traceable" a real, auditable property.

```jsonc
{
  "asset_id": "spr_mario_news_anchor",
  "asset_type": "sprite",                 // sprite | background | audio | tilemap | palette
  "status": "ready",                      // extracting | verifying | verified | curated | ready | rejected | downgraded
  "provenance": {
    "rom_title": "SUPER MARIOWORLD",
    "rom_hash_sha256": "…",               // source ROM fingerprint
    "rom_path_sanitized": "super-mario-world.sfc",
    "snes_address": "0x0DAC000",          // real SNES address+bank
    "rom_file_offset": 142606336,         // resolved via correct LoROM/HiROM map
    "extraction_method": "tilemap-walk",  // pointer-chase | documented-offset | structural-search | cgram-dump
    "extraction_method_detail": "BG1 tilemap @0x3D800 → GFX ptr → 4bpp tiles",  // human+code reproducible
    "decoder": "4bpp planar × 8×8",       // what actually decoded the bytes
    "source_bytes": { "offset": 142606336, "length": 4096, "sha256": "…" }  // exact byte range extracted
  },
  "artifact": {
    "path": "assets/sprites/mario_news_anchor.png",
    "sha256": "…",                        // content fingerprint of the artifact
    "dimensions": [32, 32],
    "palette_ref": "pal_mario_subpalette_0",
    "loop": null,                          // audio only
    "duration_ms": null                    // audio only
  },
  "palette": {
    "source": "cgram-dump@reset-routine", // real CGRAM image, not arbitrary ROM slice
    "palette_sha256": "…",
    "master_broadcast_palette": "pal_90s_primary",  // if remapped, the deterministic remap target
    "remap_recorded": true
  },
  "verification": {
    "round_trip_integrity": true,
    "noise_battery": { "all_passed": true, "checks": { "alpha_coverage": 0.34, "used_colors": 9, "tile_entropy": 3.2, "bbox_ratio": 0.6 } },
    "integration_smoke": "passed"          // survived a live render/play test in a broadcast frame
  },
  "curation": {
    "verdict": "curated",
    "role": "news-anchor-idle",
    "notes": "real SMW rest pose; placed on news-desk ground line; faces camera",
    "reviewed_at": "2026-08-13T…"
  },
  "broadcast_usage": [{ "show": "morning_news", "slot": "anchor_idle", "last_used": "2026-08-13T…" }]
}
```

**Schema guarantees:**
- **Traceability:** `provenance.source_bytes.sha256` + `rom_hash` let you re-derive the asset bytes from the ROM and prove provenance. If it can't be re-derived, it's not authentic.
- **No false-green:** `status` only reaches `ready` after `verification.noise_battery.all_passed: true` AND `curation.verdict: curated` AND `integration_smoke: passed`. No heuristic can set any of these.
- **Audit:** rejected/downgraded records stay with their reason (matching FULL_VISION's "downgrade to verified versions and document the learning").
- **Renderer contract:** broadcast reads only `status == ready` records; everything else is quarantined and never scheduled.

---

## Best next action for the builder

**Do not run the old extractors again.** They cannot produce authentic assets because the address/palette discovery is structurally wrong (R1/R2). The one change with the highest leverage:

> **Build a single "hardware-honest" provable extractor for ONE flagship game (Super Mario World), prove it end-to-end to `ready`, and only then generalize.**

Concretely, in order:
1. **Extract a real CGRAM palette the right way** — either an emulator RAM/VRAM snapshot (snes9x/mesen-s `.spc`/debugger save) or by disassembling the game's palette-init routine (search for `$2121` + `$2122` writes) — never the `0x21200` ROM slice. This unblocks *every* sprite/background's colors.
2. **Decode SMW sprites via the real tilemap walk** (BG1 tilemap @0x3D800 → tile indices → GFX pointer table → 4bpp planar tiles), with the **round-trip check** (re-encode → byte-equal) as the proof the address is real.
3. **Stand up the noise battery + catalog schema (Sections 4–5) for these few assets** and get them to `ready`; this becomes the gate every later asset must pass.
4. **Add the render-stage Red/Green guard** so a non-`ready` asset can never draw (fails to color-bars, per the vision).
5. Only at that point, extend the same *hardware-honest* path to more games — and **mechanically reject** any future asset whose provenance shows a guess heuristic (round-number offset, no method, no source-byte hash) instead of a real extraction method.

First milestone to ship: **"SMW Mario + news-desk background + one looped jingle, all three to `ready`, rendered in a live broadcast slot with a traceable manifest."** That is the first honest pixel on TV.
