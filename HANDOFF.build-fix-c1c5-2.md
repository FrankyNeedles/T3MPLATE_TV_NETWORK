# HANDOFF — build-fix-c1c5-2 (BUILDER fix pass)

> Builder worker pass on branch `build-fix-c1c5-2`. Independent audit identified
> 5 clusters (C1–C5). Two REAL root causes were present in the tree at HEAD
> `3c742e4`; fixing them flipped the full suite from 33 failing → 0 failing.
> No test was weakened or deleted — only `tvn/assets.py` and `tvn/gary.py` were
> changed (verified: `git status` shows no `tests*` edits).

## Root-cause summary (what was actually broken)

The 33 failures collapsed into **two** root causes:

1. **`tvn/assets.py` drifted** — the restored module was missing the SNES-15bit
   palette gate, `reset_gate_state()`, and catalog content-hash dedup that the
   asset-authenticity tests (`test_asset_gate.py`, `test_tilemap.py`) exercise.
2. **`tvn/gary.py::decide()` unpacked a variant as a single pair** —
   `speaker, line = rng.choice(variants)` assumed a variant was one
   `(speaker, line)` tuple, but `FALLBACK_BEATS[*]["variants"]` is a *list of
   lists of tuples* (a feud/friendship is a two-liner). This raised
   `AttributeError: 'tuple' object has no attribute 'replace'` and cascaded into
   21 tests across C3/C4/C5.

Not present in this tree (verified, so not fixed as "broken"): the `sessionCommit`
typo, the `_maybe_tick` 3600s sleep, and the `_airing_delta` saturation the audit
named — `world.py`, `runner.py`, `renderer.py` were already correct and their
failures were cascade effects of the `decide()` crash.

## Per-cluster changes

### C1 — asset-gate SNES palette fidelity (`tvn/assets.py`)
- Added `_check_snes_palette_fidelity(img)` (`assets.py:38`) — verifies every
  opaque pixel's RGB channels are a multiple of 8 (SNES 15-bit, {0,8,…,248}).
- Folded into `gate_image(kind="background")` as `checks["snes_palette_validity"]`
  and into `all_passed` (`assets.py:78-84`). Interpolated captures (e.g. RGB
  (0,0,1) or (200,3,120)) are quarantined.
- Added `reset_gate_state()` no-op (`assets.py:26`) for backward compatibility
  (gate stack has no cross-call mutable state).

### C2 — catalog content-hash dedup + tilemap distinctness (`tvn/assets.py`)
- `build_catalog()` now dedups byte-identical real-capture backgrounds: a
  per-build `seen_bg` set quarantines the second SMW screenshot with
  `gate_reason="duplicate"` (`assets.py:293-314`). Only the *real emulator-capture*
  loop dedups (`dedup=False` for procedural fallbacks), so legitimately-constructed
  sets are never false-flagged `duplicate`.
- The 8 `tilemap.constructed_set` images are SNES-15bit by construction → they pass
  the new gate → the 8 pairwise-distinct / single-set tests go green.

### C3 / C4 / C5 — Gary decide loop + per-airing beat rotation (`tvn/gary.py`)
The `decide()` dialogue builder now iterates over **every** `(speaker, line)` pair
in the chosen variant, resolving placeholders (`{a}`/`{b}`→real feud/friendship
actors, `{c1}`/`{c2}`/`{host}`→drawn hosts) per line and emitting one
`broadcast.Beat` per pair (`gary.py:236-270`). This fixes:
- **C3** — feud beats now actually populate `fills["a"]`/`fills["b"]` with the real
  feud actors and render "bowser" (etc.) in dialogue (`test_beat_caused_by_world_feud`,
  `test_feud_references_real_world_feud_actor`).
- **C4** — preset show hosts stay the primary speakers; a feud does not repin them
  (`test_decide_keeps_show_hosts_not_feud_override`). `_maybe_tick` unaffected.
- **C5** — `_choose_beat` now rotates the **priority** of the non-relational beats
  (gag/ratings/show_promo) per airing via a seed-shuffled `tail` list
  (`gary.py:152-176`), so a fresh seed yields a different beat AND variant —
  killing the byte-identical loop (`test_different_seeds_produce_different_dialogue`,
  `test_rendered_frame_is_snes_palette`, consecutive-airing background variation).
  Relational/feud beats keep top priority (unchanged), so WEAK-1a/b format
  coherence is preserved.

## Evidence (gates run live)

### Full suite (green gate, from worktree root)
```
$ python -m pytest -q                 # 132 passed in ~138s
132 passed in 138.09s (0:02:18)       # exit 0
```

### Before / after
```
BEFORE:  132 collected,  33 failed,  99 passed   (exit 1)
AFTER:   132 collected,   0 failed, 132 passed   (exit 0)
```
All 33 previously-failing tests are green AND all 99 previously-passing stayed
green (no new failures). None of the `tests*` files were modified.

### Lint
`ruff check tvn/assets.py tvn/gary.py` shows 17 findings, **all pre-existing**
(unused `asdict`/`PAL`/`_rgb`/`animation.library`, `Optional[int]` vs `X | None`,
tz-less `datetime.now()`, postponed-annotation `Path`). `git diff` confirms none of
my added lines carry a lint flag. No `ruff --fix` run (would be a drive-by refactor
of untouched code).

## Files changed
- `tvn/assets.py` — `reset_gate_state()`, `_check_snes_palette_fidelity()`,
  `gate_image` background SNES validity, `build_catalog` per-build dedup.
- `tvn/gary.py` — `_choose_beat` tail beat-rotation (GAP-3), `decide()` multi-line
  variant dialog loop.
- `HANDOFF.build-fix-c1c5-2.md` — this file (repo convention: suffix per pass;
  did not clobber the existing stage `HANDOFF.md`).