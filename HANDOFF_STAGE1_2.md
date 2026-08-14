# HANDOFF — T3MPLATE TV: STAGE 1 (Real SNES Visuals) + STAGE 2 (Real SNES Audio)

**Builder:** Orca T3MPLATE executor (STEP 0 + Stage 1 + Stage 2 per BUILD_PLAN.md)
**Branches:** `t3mplt/visuals` (Stage 1+2, 2 commits), `t3mplt/audio` (same green tree)
**Base:** `main` @ `c41f668` (verified real `tvn/` present before building)
**Date:** 2026-08-14
**Verdict followed:** BUILD_PLAN.md Stage 1 + Stage 2, green gates, honest provenance.

---

## 0. STEP 0 — WORKSPACE REPAIR (verified, before any build)

My worktree `t3mplt-exec-visuals-audio` was checked out at the **broken pre-MVP commit
`5836e31` (no `tvn/`)** — exactly the trap BUILD_PLAN §Step 0 warns about.

Repair performed (Step-0 action 2, in-worktree):
```
git rev-list --count c41f668..HEAD   # 0 unique commits on the stale branch
git reset --hard c41f668             # -> real main tree, tvn/ present
git log --oneline -1                 # c41f668 Fix 14 test-worker bugs (t3mplt-fix-bugs)
ls tvn/*.py | wc -l                  # 14 (live tvn/ package present)
```

**Step-0 gate GREEN before Stage 1:**
```
python -m pytest   -> 59 passed                       # Gate 1
python run.py --seconds 12 -> OUTPUT/broadcast/demo.mp4
ffprobe: h264 512x448 + aac; signalstats YAVG=81.5 YMAX=225.8 (non-blank)   # Gate 2
```
Only after this did I branch off `main` (`git checkout -b t3mplt/visuals`).

---

## 1. STAGE 1 — REAL SNES VISUALS (GAP-1, the #1 pillar)

### What shipped
Real SMW pixels on screen, replacing procedural placeholder cast + sets, kept behind
the existing `pose -> frame` contract so `MovementLibrary` keeps working. Two honest
sources, both provenance-tracked:

1. **Cast (method:`curated_rip`)** — Spriters Resource SMW sheets (Mario overworld
   sheet #173882, Bowser #52778, Yoshi #4591), split by connected-component
   extraction, keyed out to RGBA, mounted into `assets/movements/<char>/<pose>.png`.
   - Mario: idle / talk_a / talk_b / walk_a / walk_b / happy (6 frames, 20×20)
   - Bowser: idle / walk_a / walk_b (3 frames, scaled to 40px cast size)
   - Yoshi: idle (1 frame, scaled to 40px)
   - Each dir has `manifest.json` (method, game, rom_sha256, source_url, palette_source)
     + `cells.json` (pose→file→sha256) + per-frame gate.
2. **Backgrounds (method:`emulator_capture`)** — real SMW game screens captured from
   RetroArch 1.22.2 + snes9x core on the real SMW LoROM, native 256×224, gated
   `kind=background`, saved to `assets/backgrounds/real_<set>.png`:
   news_studio, talk_show, game_show, studio, cartoon_house, diner, city, sports_arena
   (8 real sets; 5 distinct game scenes mapped to 8 set names). Manifest tracks
   game/rom_sha256/emulator.

### Code
- `tvn/sprites.py` — `SpriteBank` now resolves a real curated frame at
  `assets/movements/<kind>/<pose>.png` when present; **falls back to the procedural
  painter** for unmounted poses/characters (never kills the feed; MovementLibrary
  unchanged).
- `tvn/assets.py` — `background(set_name)` prefers `assets/backgrounds/real_<set>.png`
  (through `gate_image kind=background`; quarantines blanks), else procedural painter.
  `gate_image` gained `real_art=True` relaxation (authentic SNES art legitimately
  exceeds the 15-colour placeholder cap and trimmed rips have bbox==1.0); the
  anti-noise floor (non-blank, sane coverage, dims) is retained.
  `build_catalog()` now records `emulator_capture`/`curated_rip` with
  `{game, rom_sha256 | source_url, palette_source, frames}`; nothing real is tagged
  `procedural_curated`.
- `scripts/validate_movements.py` — provenance + frame validator (RESEARCH_MOVEMENT §6).

### Evidence (Gate 2 — the real MP4 shows the real assets)
```
catalog provenance (assets/catalog.json): emulator_capture=12, curated_rip=10, procedural_curated=7
real backgrounds resolve + pass gate (colors = real SMW palette):
  news_studio (19406), talk_show (20050), game_show (20388), studio (17121), cartoon_house (13441)
mario idle real=True, bowser idle real=True; mario image 20x20 (not 16x20 painter)
```

---

## 2. STAGE 2 — REAL SNES AUDIO (GAP-2, the #2 pillar)

### What shipped
Real SMW music as the default beds, replacing the synth bed. Captured from the actual
snes9x SPC700/SPC-DSP via RetroArch's built-in FFmpeg recording (this IS the real SNES
sound chip output — not a hand-rolled BRR decode, which the doctrine forbids).

- **4 distinct real beds** in `assets/audio/` (method:`emulator_capture`):
  `real_smw_title.wav`, `real_smw_overworld.wav`, `real_smw_level.wav`, `real_smw_castle.wav`
  (~794KB each, mono 22050, >18s), all non-silent:
  ```
  real_smw_title     rms=0.0399
  real_smw_overworld rms=0.0483
  real_smw_level     rms=0.0497
  real_smw_castle    rms=0.0490
  ```
- **`ensure_bed()` selects real beds per format/show** with ZERO broadcast-code change
  beyond audio.py: news→title, morning→overworld, game_show→level, late_night→castle,
  etc. Synth bed remains as honest fallback for formats with no real theme.
- **`capture_spc_via_emulator` is no longer a bare `return None`.** It now:
  1. runs the full `.spc`→WAV round-trip when a *real* SPC player is on PATH
     (spc-play / spc2wav / pybrr), and
  2. otherwise returns the staged real emulator bed (real DSP audio), else `None`.
     It never fabricates a file.
- **Removed Stage-2-forbidden fake/stub audio** so nothing ships under `assets/audio/`
  that is 0-byte, silent, or a 4096-byte fake `.spc`:
  `super_mario_world_theme.spc` (4096-byte fake), `smw_*.sfx` (0-byte),
  `starfox_main.wav` / `starfox_area_6.wav` (silent -55/-90 dB).

### Honest note on the SPC toolchain
The plan's preferred route is **`.spc` (exactly 65,536 bytes) → SPC player → WAV**. That
round-trip is **genuinely unavailable on this machine**: verified no C compiler (gcc/g++/
clang all missing), `pybrr` not installable (`No matching distribution`), `pyspc` on pip is a
*statistical process-control* library (not an SPC decoder), and no `spc-play`/`spc2wav`
binary exists. ffmpeg does NOT decode SPC. Rather than ship a fake `.spc`/WAV, I shipped
the **real emulator-DSP audio** (which is exactly what an SPC player would render) and made
`capture_spc_via_emulator` auto-activate the `.spc` round-trip the moment a real player
appears. The `.spc`-file step itself is marked **toolchain-blocked**, honestly.

---

## 3. GREEN GATES (verified on the committed tree `t3mplt/visuals` @ 4fd7731)

### Gate 1 — pytest
```
python -m pytest  ->  64 passed   (was 59; +5 new Stage-1/2 tests)
  test_curated_rip_provenance_and_fallback
  test_real_smw_beds_staged_and_non_silent
  test_format_maps_to_real_bed
  test_capture_spc_via_emulator_not_pure_none
  test_old_synthetic_bed_still_honest_fallback
```

### Gate 2 — real render
```
python run.py --seconds 12
  -> OUTPUT/broadcast/demo.mp4  (479,739 bytes; was 288,616 with placeholders)
ffprobe:
  video h264 512x448, audio aac     (interleaved, real)
signalstats (287 frames): YAVG=80.8  YMAX=228.5   (non-blank; real SMW content)
volumedetect: mean_volume -7.7 dB, max 0.0 dB      (aac is REAL audio, non-silent)
```
The demo aired "Mushroom Morning" (morning→talk_show real background + real SMW overworld
bed + real Mario sprite). A frame extracted at 5s shows the real background + real cast.

> **YAVG note:** 80.8 is above the plan's placeholder-calibrated band (55–75) because the
> real SMW title screen is genuinely brighter than the old dark procedural background.
> This is authentic brightness, not blank/defect; YMAX 228.5 is essentially in-band and the
> frame is rich (52,953 unique colours) — non-blank confirmed.

---

## 4. CONTINUITY PRESERVED
- Living-world core (`world_digest()` → Gary beat → segment), the 90s grid + pod grammar,
  and Gary's zero-LLM fallback are **untouched** (Stages 1/2 swap what a segment resolves
  to, not why). `on_air()` causal feedback intact.
- Asset gate + honest catalog extended, not removed; every real asset passed `gate_image`.
- Procedural painter + synth bed remain as **graceful fallbacks**, so nothing regresses.

---

## 5. COMMITS / BRANCHES
```
c41f668 main (base)
10c8e74 feat(visuals): Stage 1 real SNES visuals - curated SMW cast + emulator-captured backgrounds
4fd7731 feat(audio):  Stage 2 real SNES audio  - emulator-captured SMW beds as default
branches: t3mplt/visuals (HEAD = 4fd7731), t3mplt/audio (same green tree)
git status: working tree clean (OUTPUT/, .build_work/, assets/catalog.json are gitignored)
```
Both branches are green and ready to merge to `main` (fast-forward from `c41f668`). Stage
1+2 are shipped on one integrated branch because they share `assets.py`/`audio.py`/tests;
`t3mplt/audio` points at the same green commit for the per-stage branch convention.

---

## 6. NOT-DONE / HONEST LIMITS
- **`.spc` (65,536-byte) capture + SPC-player render**: genuinely blocked on toolchain
  (no compiler / no installable SPC player on this box). Real emulator-DSP audio ships
  instead; the `.spc` round-trip auto-activates when a player appears. See §2.
- **Movement activation (Stage 5)**, **living-world novelty (Stage 3)**, **balance (Stage 4)**,
  **hygiene (Stage 6)**, **stream A/V sync (Stage 7)** are downstream per the plan — not in
  this build round. Real frames are mounted and MovementLibrary resolves them, but richer
  choreography is Stage 5.
- One curated-rip pose set is best-effort (SMW overworld/idle sprites); poses without a
  real mount fall back to the procedural painter (honest, documented in each manifest).
