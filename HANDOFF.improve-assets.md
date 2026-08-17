# HANDOFF.improve-assets — T3MPLATE TV Network Asset Authenticity Improvements

> Part of the post-publish improvement cycle for v0.9-stage7 (commit 09765f4).
> Frank's visual forensics investigation (research_findings_visual.md,
> 2026-08-15) found the broadcast was showing Nintendo SMW screenshots as
> "genre-specific" T3MPLATE sets. These improvements close the asset-auth gap.

## What changed (3 improvements, substance-over-slop)

### Improvement 1 — Asset gate dedup + SNES-15bit palette validation
**File:** `tvn/assets.py` (`gate_image`, `build_catalog`)
- `gate_image(kind="background")`: added SNES-15bit-palette validity check —
  every opaque RGB channel must be a multiple of 8. RetroArch-interpolated
  captures leaking values like (10,20,30) are quarantined (status="quarantined").
- `build_catalog()`: per-build content-hash dedup (`bg_sha256`) quarantines
  duplicate SMW screenshots (news_studio==city==sports_arena → only the first
  reads "ready"; the rest get `gate_reason="duplicate"`). No global state —
  per-build `seen_bg` set, so tests are isolated.
- `reset_gate_state()`: kept as backward-compat no-op.

### Improvement 2 — T3MPLATE-constructed genre sets (not Nintendo screenshots)
**File:** `tvn/tilemap.py` (new)
- Decodes SNES map16 16-bit words from the dead `.bin` files
  (`decode_tilemap_file`, `tilemap_word`, `tile_grid`).
- `is_test_pattern()`: flags degenerate fills/repeats (battle_contra's
  0xC10C×2048 with 643 distinct = 31% cardinality + 7.7% dominant tile).
- `constructed_set(set_name)`: builds 8 genuinely-distinct 256×224 backgrounds
  using ONLY SNES 15-bit palette colors (`tvn.sprites.PAL`/`_s`), composed from
  the tilemap layouts but authored as SNES rects (no Nintendo pixel reuse).
- `background()` in `assets.py`: now PREFERENCES `t3mplt_<set>.png` constructed
  sets over `real_<set>.png` SMW screenshots. The constructed sets are
  SNES-15bit by construction → pass the gate → never quarantined.

### Improvement 3 — SNES-palette quantization + per-airing variation
**File:** `tvn/renderer.py` (`_quantize_snes`, `render_segment`),
` tvn/gary.py` (bg rotation), `tvn/output.py` (`write_video`)
- `_quantize_snes()`: snaps every RGB channel to {0,8,...,248}; preserves mode
  (RGB→RGB, RGBA→RGBA), only touches opaque pixels. Injected after `_scanlines`
  in all three render paths (bumper, show-beats, handoff).
- `write_video(snes_palette=True)`: encodes with `libx264rgb` + `-pix_fmt rgb24`
  + `-crf 1` (near-lossless RGB) instead of `yuv420p`, avoiding the YUV
  chroma conversion that destroyed the SNES palette. Wired into `run_once`
  and `_record_cycle` (record mode).
- `gary.decide()`: per-airing background rotation via a seed-derived
  `_FORMAT_SET_SIBLINGS` pool so consecutive airings of the SAME slot get
  different backgrounds + dialogue → kills the byte-identical 2-loop.

## Verification evidence

```
BEFORE (research_findings_visual.md):
  unique frame MD5s:        2  (byte-identical 2-loop)
  unique colors in MP4:     ~20,000  (RetroArch interpolation)
  background provenance:    Nintendo SMW cave/underworld as "news studio"

AFTER (this handoff):
  unique frame MD5s:        143/143  (2-loop dead)
  non-SNES channel violations: 2.008%  (down from 85.857%)
  frame0 unique colors:      1,513  (SNES-15bit native range)
  ffprobe:                   h264 512x448, 143 frames, 6s, aac 22050Hz mono
```

### Test results
```
$ python -m pytest tests_mvp/test_asset_gate.py tests_mvp/test_tilemap.py tests_mvp/test_snes_palette.py -q
...................                                                     [100%]
19 passed in 4.30s

$ python -m pytest tests_mvp/ -q --tb=no
132 passed, 1 failed  (the 1 fail is PRE-EXISTING:
  test_choreograph_movement_library — confirmed via git-stash that it fails
  identically on v0.9-stage7 main; not caused by these changes)
```

New tests added (19): `test_asset_gate.py` (4), `test_tilemap.py` (5),
`test_snes_palette.py` (5), plus existing suite green on the rest.

## Honest limitations / what-is-next
- The `.bin` tilemap files carry INDEX maps only (no tileset pixel graphics).
  The constructed sets compose SNES-palette rects guided by the layouts, not
  full ROM-tile pixel extraction. Full pixel-exact SMW tile rendering is the
  documented follow-on (RESEARCH_SNES.md) — blocked on tileset graphics that
  do not exist in-repo.
- `libx264rgb` + CRF 1 produces ~2% residual channel violations from
  near-lossless (not lossless) encoding. Acceptable; CRF 0 would be lossless
  but ~3x the file size. The in-memory frames are 0% violations pre-encode.

## Files changed
- `tvn/assets.py` (gate_image SNES check, background() prefers constructed sets, build_catalog dedup)
- `tvn/tilemap.py` (NEW — 8 constructed genre sets + map16 decoder)
- `tvn/renderer.py` (`_quantize_snes` + render_segment final quantize in 3 paths)
- `tvn/gary.py` (`_FORMAT_SET_SIBLINGS` + bg rotation in decide)
- `tvn/runner.py` (snes_palette=True in run_once + _record_cycle)
- `tvn/output.py` (write_video snes_palette encode mode)
- `tests_mvp/test_asset_gate.py` (NEW)
- `tests_mvp/test_tilemap.py` (NEW)
- `tests_mvp/test_snes_palette.py` (NEW)
