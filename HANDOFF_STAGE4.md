# HANDOFF — T3MPLATE TV STAGE 4: BALANCE THE WORLD (BUG-2)

**Branch:** `t3mplt/balance` (off `c30baa3` = real main @ `E:\T3MPLATE_TV_NETWORK`)
**Commits (in order):**
1. `fe48497` feat(world): mean-reverting relationship & popularity drift
2. `421201c` fix(runner): drop wall-clock hour gate so tick() runs hourly
3. `9b3ab7c` feat(world,tests): per-character popularity reversion + regression tests
4. `f892b66` test(tools): scripted long-run simulation (acceptance-1 evidence)

**Status: DONE** — green gate 1 (pytest **91 passed**) + green gate 2 (real non-blank MP4).

---

## What changed

### 1. `tvn/world.py` — `on_air`: one-way ratchet → mean reversion (BUG-2)
The old `delta = 4 if score >= 0 else -4` (+ a `tension` addend) made a
frequently-airing pair **drift monotonically to a ±100 clamp**. Replaced with
pull toward a **signed baseline** (`BASELINE = 65.0`):

```
delta = K * (direc*BASELINE - score) + tension * TK * direc     # K=0.12, TK=0.30
```

- `direc = +1` for friendships, `-1` for feuds (from the *current* score sign).
- Below the baseline the pull is positive (friends keep warming / feuds keep
  cooling — continuity preserved); **beyond the baseline it turns negative**, so
  a pair that gets too extreme is pulled back — it oscillates around ~±65
  instead of pinning at ±100.
- A zero net pull is nudged one point in the relationship's direction so an aired
  pair always registers (drift, not a frozen equilibrium).
- **Tension** now pushes *along the relationship's own axis* (a heated feud
  deepens, a heated friendship warms) rather than always toward +1.

**Popularity** `_pop_delta`: same philosophy, mean-reverts each co-host toward
the celebrity baseline (`_POP_BASELINE = 60.0`) from **their own** value, with a
small friend-glow / feud-face-loss bias. Fixed a latent bug: the loop previously
derived ONE shared `pop_delta` from whichever co-host, so a character at 99 could
be pushed to a clamped 100. Each co-host now reverts from its own fame → nobody
pins at 100/0.

### 2. `tvn/runner.py` — `_maybe_tick`: drop the {2,3,4} wall-clock gate (BUG-2)
The old code ran `world.tick()` only during hours 2–4 AM; a broadcaster started
at 9am could run **for days without a tick**, so decay / career / seeking-work
evolution never happened. Now `_maybe_tick` fires `tick()` on a **monotonic
schedule (once per ~3600s) from the moment the loop starts**, regardless of the
wall-clock hour.

---

## Acceptance evidence (honest)

### Acceptance 1 — no ±100 saturation; scores oscillate near baseline
`scripts/simulate_airings.py` performs scripted long runs of the SAME pair
(400 airings + hourly tick decay, starting near the saturation edge):

```
FRIENDSHIP  mario~luigi   start +90 -> range [68, 88]   hit ±100? False
            oscillations: 194 up / 205 down   final score=70
            popularity: 99 -> 73 (reverted, not pinned)
FEUD        mario~bowser  start -90 -> range [-88,-70]  hit ±100? False
            oscillations: 203 up / 196 down   final score=-70
            popularity: 99 -> 53 (reverted, not pinned)
```

Both cases mean-revert and **oscillate** around the signed baseline; neither
clamps to ±100; popularity reverts to the celebrity baseline instead of
ratcheting to 100.

### Acceptance 2 — evolution runs at ANY start hour
Regression tests prove `_maybe_tick` ticks on its first call (no hour gate) and
again after 3600s elapse; a `pitch`→`cancellation` transition flips cast to
seeking_work on a plain `tick()`. A 9am start ticks immediately — no multi-day
stall.

### Gate 1 — pytest
```
91 passed in 15.12s   (baseline 80 → +11 new Stage 4 tests)
```
New `tests_mvp/test_stage4_balance.py` (11 tests): mean-reversion unit checks,
non-saturation/oscillation long-runs for friendship AND feud, popularity
reversion, hour-independent tick, career/seeking-work evolution. Existing
Stage 1/2/3 tests all still pass (no regression).

### Gate 2 — real non-blank MP4
```
PYTHONPATH=. python run.py --seconds 12
-> OUTPUT/broadcast/demo.mp4   (433,015 bytes)
ffprobe:  h264 512x448, duration 11.958s  +  aac audio (mono)
signalstats: 287 frames, YAVG min=45.0 max=75.6 mean=58.9  → NON-BLANK throughout
```

---

## Tradeoffs / open threads
- **Baseline magnitude is a constant (±65).** It could be derived per-relationship
  (e.g. from the seeded strength or arc_label) for more texture later; the
  current fixed signed baseline matches the critique's "drift toward baseline"
  and keeps the model simple/causal. Easy to parametrize in Stage 5+ if wanted.
- **Tension semantics changed deliberately:** it now deepens/warms along the
  relationship axis (causal) instead of always adding toward +1.
- `world.py` `on_air` popularity uses an average of the two co-hosts' deltas only
  for the log line; each character mutates by its own delta.
- The dead `app/` stack still carries unrelated collection errors (pre-existing)
  and is NOT part of this stage's gate (Stage 6 hygiene sweep targets it).

## Next best action
- **Stage 5** (ACTIVATE MOVEMENT, WEAK-2) — this stage is independent of the
  balance changes; the movement library is already correct, just never driven.
- Optionally revisit baseline magnitude per-relationship in the next build.

---
Marked **done** — green gate (91 pytest + real non-blank MP4). Ready for the CC
to ingest, spin test workers for a bug-hunt pass, and close/merge the branch.