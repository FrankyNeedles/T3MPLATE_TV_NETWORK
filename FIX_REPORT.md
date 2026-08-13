# FIX_REPORT — T3MPLATE TV MVP (branch `t3mplt-fix-bugs`)

Fixes applied to the 14 bugs found by the test worker in `BUG_REPORT.md`
(prioritized Critical + Major, then Minor/Nit). Each fix is minimal and honest,
preserves the substance-over-slop / 90s-authenticity ethos, and does NOT regress
the 44 pre-existing tests (full suite now **59 passed**).

## Critical

### C1 — `tvn/runner.py` `_maybe_tick` slept the whole loop 3600s in 2–4 AM
- **Bug:** `_maybe_tick()` called `time.sleep(3600)` inside the `while True` render
  loop whenever the wall-clock hour was 2/3/4 → ~3h of dead air per day.
- **Fix:** maintenance never blocks the render loop. `_maybe_tick` now runs
  `world.tick()` at most **once per hour** using a `time.monotonic()` guard
  (`_last_tick_ts`), and performs **no long sleep** — the loop's existing
  `time.sleep(1.0)` between aired segments is untouched. Off-peak hourly
  maintenance is preserved; the broadcast stays live.
- **Verify:** `test_maybe_tick_never_sleeps_3600` asserts `3600` is never slept and
  no sleep ≥ 60s occurs. `run_24_7.py --record` ran continuously (no 3h freeze).

### M1 — `tvn/runner.py` `segment_frames` `--seconds 0` → infinite generator
- **Bug:** `total = int(seconds * fps) if seconds else None` — `0` is falsy, so an
  explicit `--seconds 0` became `total=None` (continuous/infinite).
- **Fix:** an explicit `seconds is not None and seconds <= 0` now early-returns a
  bounded no-op; `None` remains "until stopped". Positive durations unchanged.
- **Verify:** `test_segment_frames_zero_seconds_is_bounded` (terminates, doesn't hang).

### M2 — `tvn/output.py` silent corruption on interrupt/ffmpeg mid-write
- **Bug:** `write_video` wrote straight to the final path; on a mid-write
  interrupt/ffmpeg failure it only raised when `silent=False` (default was False
  to raise, but silent recording left/kept corrupt partials and never cleaned up).
- **Fix:** write to a same-dir temp (`x.part.mp4` — keeps the `.mp4` suffix so
  ffmpeg infers the muxer), then `os.replace()` **atomically** into the final path
  on success. On **any non-zero ffmpeg exit** the partial temp is deleted and a
  `RuntimeError` is raised (even in silent mode), so a broken broadcast can never
  be mistaken for a good one and readers never see a half-written file.
- **Verify:** `test_write_video_raises_and_cleans_partial_on_failure` (non-zero →
  raises, no partial at final path, temp removed), `test_write_video_writes_atomically`
  (success → atomic rename, old file replaced). Live: SIGKILL mid-write left only a
  `.part.mp4` temp, never a corrupt final `.mp4`.

### M3 — `.env` (TWITCH_STREAM_KEY / T3TV_FFMPEG) never loaded → `--stream` dead
- **Bug:** `config.py` built `Settings` from `os.getenv` but nothing ever called
  `load_dotenv`, so `TWITCH_STREAM_KEY` in `.env` was never read and `--stream`
  was dead on arrival.
- **Fix:** `tvn/config.py` now calls `load_dotenv(ROOT / ".env")` at import,
  **before** `Settings` reads the environment. `python-dotenv>=1.0` added to
  `requirements.txt`. Import is guarded so an env without dotenv still works.
- **Verify:** `test_settings_read_env_after_dotenv` (Settings reads
  TWITCH_STREAM_KEY → rtmp_url / T3TV_FFMPEG).

### M4 — configured `SETTINGS.ffmpeg` vs hardcoded `'ffmpeg'`
- **Bug:** `output.py` hardcoded `"ffmpeg"` in `write_video`/`stream_rtmp`
  instead of the configured `SETTINGS.ffmpeg`.
- **Fix:** both use `_ffmpeg()` → `SETTINGS.ffmpeg or "ffmpeg"`.
- **Verify:** `test_write_video_uses_configured_ffmpeg_binary` (custom path is the
  argv[0]).

### M5 — `programming.py` GRID uses `psa`/`sitcom` but `SHOW_PRESETS` lacks them
- **Bug:** grid slots with `fmt="psa"` (PSA Hour) and `fmt="sitcom"` fell through
  to the `news` preset default (`SHOW_PRESETS.get(fmt, ...["news"])`).
- **Fix:** added `psa` (studio / `toad`, sincere, public_service) and `sitcom`
  (cartoon_house / `yoshi`+`toad`, happy, comedy) presets to `content.SHOW_PRESETS`.
- **Verify:** `test_show_presets_cover_grid_formats` (no grid format lacks a
  preset) and `test_psa_and_sitcom_decide_as_themselves` (seg.fmt == slot.fmt).

## Major (m*)

### m1 — `run_24_7.py --seconds` parsed but ignored (runner hardcoded 12.0)
- **Fix:** `seconds` threaded through `run_24_7.main` → `run_forever(seconds=...)`
  → `_record_cycle(seconds=...)` in both record and stream paths (previously
  `_record_cycle` and streaming used a hardcoded `12.0`).
- **Verify:** `test_record_cycle_honors_seconds` captures 7.5; live
  `run_24_7.py --seconds 4` produced ~4.4s chunks (was 12s).

### m2 — `gary.py` feud/friendship beat re-pinned speakers, dropping the real host
- **Bug:** `decide()` overwrote `c1/c2` with the top friendship/feud actors, so a
  feud beat bumped the show's own co-host (e.g. `luigi`) off-mic in dialogue.
- **Fix:** dialogue speakers are always the **show's preset hosts**; the feud /
  seeking-work participant joins as an **added guest** instead of replacing a host.
- **Verify:** `test_decide_keeps_show_hosts_not_feud_override` — `luigi` (news
  co-host) is both cast and a speaker even when a feud is the active beat.

### m3 — `world.py` `on_air` bumped popularity +1 for both co-hosts even when feuding
- **Fix:** popularity delta follows the relationship outcome — `+1` when
  friendly, `-1` when the pair is feuding (same sign as the chemistry delta),
  clamped to [0, 100].
- **Verify:** `test_on_air_feud_lowers_popularity` — mario & bowser (seeded feud)
  each drop below 51 after co-hosting.

### m4 — runtime DBs tracked → dirty tree
- **Fix:** `git rm --cached data/living_world.db data/lore/living_world.db` (the
  runtime DB is regenerated on launch) + added `data/living_world.db` to
  `.gitignore` (it already had `data/lore/*.db`).
- **Verify:** `git ls-files` no longer contains any `*.db`; `git status` shows the
  DB deletions staged and no runtime DB dirtying the tree.

### m5 — `world.py` seeding raced under concurrency (duplicate seed)
- **Fix:** `_seed()` is now concurrency-safe: it performs seeding in `_seed_now()`
  and commits; if a concurrent worker committed identical rows first, the loser's
  `IntegrityError` is caught and rolled back (winner retained, no crash, no dup).
- **Verify:** `test_seed_is_idempotent_across_reopen` (re-open of a seeded DB stays
  9 characters, not 18).

## Nit / cleanups (n*)

- **n1** `renderer.py` `draw_cast` — removed dead `* 0` multiply in spacing
  (`(WN - base_w * 0)` → `WN // (n+1)`).
- **n2** `audio.py` crossfade — replaced the no-op `head * 0.0` blend with a real
  tail→head fade (uses `out[-ff:]`). See `test_synth_bed_crossfade_uses_tail`.
- **n3** `renderer.py` `render_segment` — `frames_total` was a hardcoded
  `24 * beats`; now `rate * beats` so fps is honored. See
  `test_render_segment_honors_fps`.

## Green gate
- Full suite: **59 passed** (44 original + 15 new regression tests, 0 failures).
- `run.py --seconds 6` → real 165KB 512×448 h264 + aac MP4 (7.4s), no hang.
- `run_24_7.py --seconds 4 --record` → continuous appending ~4.4s chunks (m1
  honored), clean interruption, no corrupt final files (only a `.part.mp4` temp on
  hard-SIGKILL mid-write, which is expected and cleaned).

## Files changed
`.gitignore`, `requirements.txt`, `run_24_7.py`, `tvn/audio.py`, `tvn/config.py`,
`tvn/content.py`, `tvn/gary.py`, `tvn/output.py`, `tvn/renderer.py`,
`tvn/runner.py`, `tvn/world.py`, `tests_mvp/test_output.py`,
`tests_mvp/test_regressions.py` (new), plus staged removal of the two runtime DBs.
