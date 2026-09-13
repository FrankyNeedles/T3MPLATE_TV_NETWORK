# LIFECYCLE_REPORT — Series Lifecycle Engine + Sweeps Wiring (BUILD_SCOPE #1)

**Branch:** `build-t3mplate-lifecycle`
**Commit:** `9542e1b` — `feat(lifecycle): wire full series lifecycle engine + sweeps wiring`
**Gate:** `144 passed` (132 baseline + 12 new lifecycle tests) — zero regressions.

---

## Task

BUILD_SCOPE.md **Improvement #1 (P0, highest leverage)**: convert a merely
*"running"* broadcast (airs slots, advances episodes, drifts relationships) into a
*LIVING* one — where series are actually **born, ordered, cancelled, syndicated,
and revived** by the world.

> Root cause (recorded in BUILD_SCOPE): `tick()` (`world.py`) had a
> pitch→cancellation→syndication skeleton, but **no show was ever seeded
> `status="pitch"`** — every seeded show was `status="series"` and `on_air()`
> upserted as `series`. The `filter_by(status="pitch")` query matched zero rows.
> `tick()` was **dead code** for lifecycle. `SeasonState` was flavor. `bump_gag`
> had **zero callers**.

---

## What changed

### `tvn/world.py` — the core engine
- **Mint pitch shows** — a relationship with a directed `arc_label` whose bond is
  strong (`|score| > 50`) and no active show carries that arc → spawns a
  `pitch` show with the pair as hosts. This is what makes `tick()` **BIRTH** shows.
- **Pilot phase** — a *pre-existing* pitch → `pilot` (seed rating ≥ 6.0) or
  `cancellation` (weak). A pitch **never** goes straight to cancellation.
- **Pilot → series / failure** — 3-airing pilot window AND rating ≥ 6.5 → series;
  rating < 5.5 → cancellation.
- **Series → syndication** — now gated (≥ 8.0 rating **and** ≥ 10 eps), no longer
  unconditional.
- **Series → cancellation** — rating ≤ 4.0.
- **Cancellation → revival** — **only** in a sweeps month (7/10/11/12) **and**
  rating ≥ 7.5.
- **Career evolution (in `on_air`)** — regular→star (≥ 8.0), star→legend (≥ 9.0,
  sets `retired=True`, kept in history, out of the active cast pool), star→regular
  (≤ 3.0); `show_count` accumulates per airing; career rating mean-reverts toward
  6.0 (never pins).
- **Gag tracking** — `bump_gag(...)` gains its first real callers.
- **Career model** gains a `retired` column (migration in `_ADD_COLUMNS`).
- **`morning_report()`** now surfaces `lifecycle` (per-status show counts) and
  `lifecycle_events` (recent pitch/pilot/syndication/cancellation/revival events).

### Sweeps wiring
- `tvn/content.py` — `SWEEPS_MONTHS {7,10,11,12}` and `SWEEPS_STUNTS` (month →
  stunt titles); `stunt` added to the allowed beats for talk/game_show/late_night/
  sitcom/action; a `stunt` beat template in `FALLBACK_BEATS`.
- `tvn/gary.py` — `_choose_beat` airs a **`stunt` beat first** during a sweeps
  month (outranks routine relational drama).
- `tvn/programming.py` — `build_pod(..., season=)` injects a SWEEPS STUNT promo
  into a commercial pod during a sweeps month.
- `tvn/runner.py` — `_maybe_tick` adds a **night-shift morning-report** branch
  (pre-dawn hours 2–4 → writes `OUTPUT/morning_reports/latest.json`).
- `run.py` — advances the lifecycle before recording so the demo surface the
  living engine (pitch births) in the morning report.

### Tests
- **`tests_mvp/test_lifecycle.py` (12 tests, new)** — covers the full acceptance
  set: mint-from-storyline, pitch→pilot, syndication rating gate, sweeps revival,
  career regular→star, gag on-air increment, cancelled-cast seeks work, stunt
  content + pod injection, Gary stunt beat, full pilot→series promotion, and
  star→legend retirement.
- **Reconciled** `test_stage4_balance.py::test_career_seeking_work_evolves_at_any_hour`
  — the old assertion relied on the removed dead-code path (pitch→cancellation→
  seeking work). Under the new contract, seeking-work is driven by a **cancellation**
  (series rating ≤ 4.0). Updated to cancel a show whose host (yoshi) holds no other
  live engagement, preserving the test's intent.

---

## Green-gate evidence (real output)

### Gate 1 — full suite
```
144 passed in 114.10s
```
(132 baseline + 12 new lifecycle tests; zero failures, zero regression.)

### Gate 2 — seeking_work-on-cancellation gap (explicitly verified)
```
tests_mvp/test_lifecycle.py::test_cancelled_show_cast_seeks_work ... PASSED
tests_mvp/test_lifecycle.py::test_career_promotes_regular_to_star ... PASSED
tests_mvp/test_lifecycle.py::test_cancellation_revives_only_in_sweeps ... PASSED
```

### Gate 3 — end-to-end broadcast (`run.py --seconds 12`, fresh DB)
```
Broadcast recorded -> OUTPUT/broadcast/demo.mp4 (502652 bytes)
ffprobe: codec_name=h264, width=512, height=448, avg_frame_rate=24/1; codec_name=aac
MORNING REPORT:
  shows: 10 | relationships: 8
  lifecycle: pitch:3, series:7
  [LIFECYCLE] network pitches 'mario & bowser: The Eternal Rivalry' from ...
  [LIFECYCLE] network pitches 'link & zelda: Hyrule Trust' from ...
  [LIFECYCLE] network pitches 'mario & luigi: Brothers Reunited' from ...
```
Non-blank, real h264+aac MP4, and the morning report surfaces a **lifecycle event**
(pitch birth) — the exact symptom that proved tick was dead before.

### Gate 4 — `bump_gag` has ≥ 2 callers
```
tvn/world.py:597  self.bump_gag(gag.gag_text)   # on_air (item 8)
tvn/world.py:670  self.bump_gag(gag.gag_text)   # seek-work cancellation tick path
```

### Gate 5 — lifecycle genuinely advances over repeated ticks
```
after tick 1: {'pitch': 3, 'pilot': 0, 'series': 6, ...}
after tick 2: {'pitch': 0, 'pilot': 3, 'series': 6, ...}
after tick 3: {'pitch': 0, 'pilot': 3, 'series': 6, ...}   # advances on window+rating
```
Pitch shows are minted, promote to pilot, and proceed to series once the pilot
window + rating gate are met.

---

## Quality / hygiene notes (honest)

- **`world.py`: 0 mypy errors** after the rewrite (the career block was initially
  placed as a sibling of `if show:` — a latent `NameError` when `show=None` — mypy
  caught it and it was re-indented inside `if show:`, which also restores type
  narrowing).
- **New test file lint-clean**; full-suite ruff at **105 errors**, *below* the
  documented 106-error pre-existing DTZ baseline — the change adds **zero net**
  lint errors (remaining are the codebase's established naive-datetime style).
- Pre-existing mypy errors in `config.py`/`assets.py`/`renderer.py`/`output.py`/
  `sprites.py` and `runner.py:32,109` are untouched and out of scope.
- `tests_mvp/test_lifecycle.py` was normalized to CRLF (repo convention) before
  commit to avoid line-ending churn.

## Scope boundaries
- In scope: BUILD_SCOPE #1 lifecycle engine + sweeps wiring + the 12-test suite.
- Not in scope (later improvements): commercial-pod **rendering** (#2), real SNES
  audio/visuals, RTMP-twitch exercise. The `commercial` flag is still set but not
  yet rendered into frames (documented BUILD_SCOPE #2).
- Working tree is **clean** at commit `9542e1b`.