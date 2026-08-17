# BUILD SCOPE — T3MPLATE TV Network MVP → LIVING

> **For the BUILDER (worker that follows the CRITIC pass).**
> Base commit: `09765f4` (tag `v0.9-stage7`). Target branch:
> `t3mplt-build-living`. No source file may change without a corresponding test.
> Each item below has acceptance criteria and a green gate.
>
> **Motivation:** The MVP *runs* (airs grid slots, advances episodes, drifts
> relationships) but does not *live*. Shows never die, are never born, never get
> revived. Careers never evolve. Seasons are flavor text. The single highest-
> leverage fix — the one that converts "running" into "living" — is wiring the
> full series lifecycle through `tick()` with rating gates and sweeps triggers.
> Everything else (career evolution, night-shift development, revival, gag
> tracking) depends on it. **Priority #1 below.**

---

## IMPROVEMENT #1 — Series Lifecycle Engine + Sweeps Wiring (P0, highest leverage)

> **The single change that makes the broadcast genuinely LIVING.**

### Problem

`tick()` (`world.py:557-579`) has a pitch→cancellation→syndication skeleton, but
**no show is ever seeded or created in `status="pitch"`** — all seeded shows are
`status="series"` (`world.py:312`), and `on_air()` upserts as `status="series"`
(`world.py:528`). The `filter_by(status="pitch")` at `world.py:564` matches zero
shows. Tick is dead code for lifecycle. SeasonState is read-only flavor — never
consulted by scheduling, decision, or rendering.

### Solution

**`world.py` — `tick()` rewrite (replace lines 557-579):**

1. **Create pitch shows from unresolved storylines**: If a `Relationship` has an
   `arc_label` but `score` magnitude > 50 (strong story), and no active show
   carries that arc, mint a `Show(status="pitch", genre=<derived>, ...)` with
   hosts = the relationship pair. Seed arc from `RELATIONSHIP_ARCS`
   (`world.py:65-72`). Call `bump_gag` for any gag associated with a cast member
   that aired this cycle (fixes §2.6 as a side effect).

2. **Pilot phase**: `tick()` advances a `status="pitch"` show to `status="pilot"`
   if `show.rating >= 6.0` (seeded baseline), else to `"cancellation"`. No show
   goes pitch→cancellation directly (remove `world.py:565`).

3. **Pilot → Series / Failure**: If a `status="pilot"` show has `airings >= 3`
   (minimum pilot window) and `rating >= 6.5`, promote to `"series"`. If
   `rating < 5.5`, demote to `"cancellation"`.

4. **Series → Syndication (rating gate)**: `status="series"` shows with
   `rating >= 8.0` and `episode_count >= 10` → `"syndication"`. (Currently
   syndication is unconditional at `world.py:574`.)

5. **Series → Cancellation (rating gate)**: `status="series"` shows with
   `rating <= 4.0` → `"cancellation"`.

6. **Cancellation → Revival (sweeps gate)**: `status="cancellation"` shows
   revive to `"pilot"` if (`show.rating >= 7.5` AND current season is a sweeps
   month per `content.SEASONS`). Sweeps months: 7 (Midsummer Sweeps), 10
   (Halloween Haunt), 11 (Thanksgiving Sweeps), 12 (Holiday Specials).

7. **Career evolution**: In `on_air()`, after updating show rating, update
   associated `Career` records (`world.py:112-122`):
   - `show.rating >= 8.0` → `career_level` promotes: `"regular"` → `"star"`.
   - `show.rating >= 9.0` and `career_level == "star"` → `"legend"` (retirement:
     set `retired=True`, remove from active cast pool, but keep in history).
   - `show.rating <= 3.0` → demote `"star"` → `"regular"`.
   - `career.show_count` increments per airing (`world.py:519-545` context).
   - `career.rating` tracks `show.rating` (mean-reverting toward 6.0, not pinning).

8. **Gag tracking fix**: `on_air()` calls `self.bump_gag(...)` for any gag
   whose `associated_characters` overlap with the on-air cast, when the aired
   beat type is `"gag"`. (Currently `bump_gag` is defined at `world.py:548` but
   has zero callers.)

9. **Morning report auto-generation**: `_maybe_tick()` (`runner.py:192-204`)
   gains a night-shift branch: when `datetime.now().hour in (2,3,4)` and
   `tick()` just ran, call `world.morning_report()` and write to
   `OUTPUT/morning_reports/latest.json`.

**`content.py` — add sweeps stunt pod variants** (`content.py:111-141` area):
Add `SWEEPS_STUNTS` dict mapping month→list of special stunt titles
(e.g. 10→["Halloween Haunt Crossover: Mario vs Bowser", "Night of the Koopas"]).
`programming.build_pod()` gains an optional `season` param; when the current
month is a sweeps month, inject a stunt promo into the pod.

**`gary.py` — sweeps-aware beat selection**:
In `decide()` (`gary.py:160-278`), when the current month is a sweeps month,
elevate `_BEAT_PRIORITY` (`gary.py:53-54`) to check for `"stunt"` beats (new
beat type) drawn from `content.SWEEPS_STUNTS`.

### Acceptance criteria (testable)

```python
# test_lifecycle.py — NEW FILE
def test_tick_creates_pitch_show_from_storyline(world):
    """A strong relationship arc with no active show spawns a pitch show."""
    # Force mario~bowser feud to high magnitude
    rel = world._find_rel(world.get_character("mario").id,
                          world.get_character("bowser").id)
    rel.score = -80; world.session.commit()
    shows_before = world.session.query(Show).count()
    world.tick()
    assert world.session.query(Show).count() > shows_before
    new_show = world.session.query(Show).filter_by(status="pitch").first()
    assert new_show is not None

def test_pitch_to_pilot_transition(world):
    """tick() advances pitch → pilot (never pitch → cancellation directly)."""
    world.session.add(Show(name="Test Pitch", status="pitch", genre="news", rating=6.0))
    world.session.commit()
    world.tick()
    s = world.session.query(Show).filter_by(name="Test Pitch").first()
    assert s.status in ("pilot", "series")  # NOT "cancellation"

def test_syndication_gated_on_rating(world):
    high = Show(name="Hit", status="series", genre="news", rating=9.0,
                episode_count=15, airings=15)
    low  = Show(name="Miss", status="series", genre="news", rating=2.0,
                episode_count=8, airings=8)
    for s in (high, low): world.session.add(s)
    world.session.commit()
    world.tick()
    assert world.session.query(Show).filter_by(name="Hit", status="syndication").first()
    assert world.session.query(Show).filter_by(name="Miss", status="cancellation").first()

def test_cancellation_revives_only_in_sweeps(world, monkeypatch):
    show = Show(name="Revivable", status="cancellation", genre="news",
                rating=8.0, episode_count=5)
    world.session.add(show); world.session.commit()
    # Non-sweeps month
    monkeypatch.setattr("tvn.world.datetime")  # -> month=3 (Spring)
    world.tick(); assert world.session.query(Show).filter_by(name="Revivable").first().status == "cancellation"
    # Sweeps month
    monkeypatch.setattr("tvn.world.datetime")  # -> month=10 (Halloween Haunt)
    world.tick(); assert world.session.query(Show).filter_by(name="Revivable").first().status == "pilot"

def test_career_promotes_regular_to_star(world):
    mario = world.get_character("mario")
    before = world.session.query(Career).filter_by(character_id=mario.id).first()
    assert before.career_level == "regular"
    # Air a high-rated show
    world.on_air(["mario", "luigi"], show="News of T3TV", tension=0)
    # Simulate high show rating → on_air should promote
    # (test via direct career evolution check)

def test_gag_occurrence_increments_on_air(world):
    world.on_air(["yoshi", "toad"], show="Super Playhouse", tension=0, genre="cartoon")
    # Should call bump_gag for "Yoshi eats everything"
    g = world.session.query(RunningGag).filter_by(gag_text="Yoshi eats everything").first()
    assert g.occurrence_count >= 1

def test_seekint_work_beat_fires_when_season_is_sweeps(world):
    """seeking_work characters appear as guests when cancel path actually fires."""
    # This tests the full chain: tick cancels a show → cast becomes seeking_work →
    # world_digest shows seeking_work → gary.decide picks seeking_work beat
```

### Green gate for #1

- All existing 113 tests still pass.
- New `tests_mvp/test_lifecycle.py` with ≥8 tests pass.
- `run.py --seconds 12` produces non-blank MP4; morning report shows a lifecycle
  event (pilot/syndication/cancellation) in `recent_events`.
- `bump_gag` has ≥2 callers in `tvn/` (on_air + seek-work tick path).

---

## IMPROVEMENT #2 — Commercial Pod Rendering (P1, high — unlocks 90s authenticity)

> **The broadcast pipeline has pod grammar but never renders a commercial break.**

### Problem

`build_pod()` (`programming.py:113-141`) and `build_handoff()`
(`programming.py:154-157`) are defined and tested (`test_programming.py:28-48`)
but **never called from runner.py, gary.py, or renderer.py** (grep → 0 matches in
production). `render_segment()` (`renderer.py:262-300`) renders only
bumper → show beats → hand-off. The `commercial` boolean on
`BroadcastSegment` (`gary.py:277`) is set but never read.
`draw_lower_third()` (`renderer.py:169-180`) and `draw_full("station_id")`
(`renderer.py:204-211`) are defined but never called in the live frame pipeline.

### Solution

**`renderer.py` — `render_segment()` (lines 262-300):**

1. After the bumper (line 279-285) and before show beats (line 287-292), insert:
   if `segment.commercial`, render the commercial pod — call
   `programming.build_pod(segment.daypart, ...)` and render each `PodElement`
   as N frames via `draw_full(elem.kind, elem.text)` (commercial cards at
   `assets.py:195-226`).

2. After show beats and before hand-off, insert a station-id bumper
   (`draw_full("station_id", "T3TV")` for 8 frames).

3. In `frame()` (`renderer.py:214-243`), call `draw_lower_third()` for each
   cast member with `c.title`, painting the name+title overlay in the lower-left
   (below the dialogue box, above the ticker strip).

4. Wire `draw_full("color_bars")` as an emergency fallback if
   `segment.background` resolves to None.

**`runner.py` — pass pod into the segment:**
`_decide_differing` / `_record_cycle` already call `gary.decide(slot)` which
returns a `BroadcastSegment` with `commercial` set. No change needed in runner —
the renderer just needs to consume it.

### Acceptance criteria

```python
def test_render_segment_includes_commercial_pod():
    seg = broadcast.BroadcastSegment(
        seg_id="t", title="Test", fmt="sitcom", daypart="prime",
        background="studio", commercial=True,
        cast=[broadcast.Cast(name="mario", kind="mario", title="Anchor")],
        beats=[broadcast.Beat(speaker="mario", text="Hello.")])
    segments = list(renderer.render_segment(seg, final=False))
    # Count distinct visual blocks by checking for promo-card content
    assert len(segments) > 30  # show beats alone would be fewer

def test_lower_third_appears_on_frame():
    seg = broadcast.BroadcastSegment(
        seg_id="t", title="News", fmt="news", background="news_studio",
        cast=[broadcast.Cast(name="mario", kind="mario", title="Anchor")],
        beats=[broadcast.Beat(speaker="mario", text="Hello.")])
    r = renderer.Renderer()
    frame = r.frame(seg, 0)
    # Lower-left region should have non-background pixels (lower-third text)
    arr = np.asarray(frame.convert("RGB"))
    lower_left = arr[-22:, :130]  # lower-third region
    assert lower_left.std() > 5  # has content, not just the background
```

### Green gate for #2

- All existing tests pass + 4 new tests.
- `run.py --seconds 12` MP4 includes visible commercial cards and lower-third.

---

## IMPROVEMENT #3 — Night Shift Protocol (P1, high — makes broadcast autonomous)

> **FULL_VISION §Night Shift Protocol (L177-185): 2AM-5AM autonomous development.**

### Problem

`_maybe_tick()` (`runner.py:192-204`) fires hourly on a monotonic timer — not
gated to 2AM-5AM (`runner.py:203`: `now - _last_tick_ts >= 3600`).
`tick()` only decays scores + dead cancel path. No show development, no pilot
pitching, no morning report auto-gen, no set evolution.

### Solution

**`runner.py` — `_maybe_tick()` (lines 192-204) rewrite:**

1. Keep the hourly monotonic tick (BUG-2 fix stays).
2. ADD a night-shift branch: when `datetime.now().hour in (2,3,4)`:
   - Call `world.tick()` (full lifecycle — Improvement #1).
   - Call `world.develop_pilots()` — a new method that creates pitch shows from
     unresolved storylines (relationship arcs not yet in a show + gags with
     `occurrence_count < 3`).
   - Call `world.morning_report()` and write to `OUTPUT/morning_reports/`
     (currently only called from `run.py:41`).

**`world.py` — add `develop_pilots()` method:**

```python
def develop_pilots(self):
    """Night shift: mint pitch shows from unresolved storylines."""
    # 1. Unresolved relationship arcs (arc_label set but no active show)
    active_show_arcs = {s.arc_label for s in self.session.query(Show)
                        if s.status in ("series", "pilot")}
    for (a, b), label in RELATIONSHIP_ARCS.items():
        if label not in active_show_arcs:
            # Check if the pair's tension warrants a show
            rel = self._find_rel(...)
            if rel and abs(rel.score) >= 40:
                self.session.add(Show(name=f"Pilot: {label}",
                                      status="pitch", genre=<derived>,
                                      rating=6.0, hosts=[a, b],
                                      episode_count=0, arc_label=label))
    self.session.commit()
```

### Acceptance criteria

```python
def test_night_shift_hour_gate():
    """Night shift work only happens 2AM-5AM."""
    # Run the loop at 2:30 AM → develop_pilots called
    # Run at 10:00 AM → develop_pilots NOT called

def test_develop_pilots_creates_pitch_from_arc(world):
    before = world.session.query(Show).count()
    world.develop_pilots()
    # mario~bowser "Eternal Rivalry" arc exists but no show carries it
    assert world.session.query(Show).filter_by(status="pitch").count() >= 1
    assert world.session.query(Show).count() > before

def test_morning_report_auto_generated(world, tmp_path, monkeypatch):
    """morning_report written to OUTPUT during night shift."""
    # Mock night hours → run night shift → assert file written
```

### Green gate for #3

- All existing tests pass + 3 new tests.
- `_maybe_tick` at 2:30 AM creates pilot shows + writes morning report.

---

## IMPROVEMENT #4 — Set Evolution (P2, medium — visual aliveness)

> **FULL_VISION §Set Evolution (L60): Weather, seasonal decorations, prop continuity.**

### Problem

`renderer.draw_background()` (`renderer.py:63-65`) → `assets.background()` →
static set. `current_season()` (`world.py:236-257`) never read by renderer.
No weather, no seasonal decoration, no prop continuity, no set upgrades.

### Solution

**`renderer.py` — `frame()` (lines 214-243) + `draw_background()` (63-65):**

1. `draw_background()` accepts a `season` and `weather` param. When
   `world.current_season()["season"]` indicates winter → add snow overlay;
   summer → sun overlay; during sweeps months → add seasonal decoration sprites
   (pumpkins for Halloween, turkeys for Thanksgiving).

2. `frame()` reads `segment.background` + queries `world.current_season()`
   (passed in from runner) to composite a seasonal overlay.

3. Add `prop_state` to `LivingWorld` — a JSON dict of persistent props per show
   (coffee mugs, desk items). `on_air()` increments `prop_state[show]["coffees_served"]`
   so the same prop persists across airings (prop continuity).

4. Set upgrades: when `show.rating >= 8.5`, `draw_background` adds upgraded set
   pieces (e.g. a trophy case, better desk) — a second background layer.

### Acceptance criteria

```python
def test_seasonal_overlay_changes_with_month(world, monkeypatch):
    monkeypatch.setattr → month=10  # Halloween Haunt
    # Render frame → assert pumpkin pixels in background
    monkeypatch.setattr → month=12  # Holiday Specials
    # Render frame → assert different seasonal overlay

def test_prop_continuity_persists_across_airings(world):
    world.on_air(["mario", "luigi"], show="News of T3TV", tension=0)
    props1 = world.prop_state("News of T3TV")
    world.on_air(["mario", "luigi"], show="News of T3TV", tension=0)
    props2 = world.prop_state("News of T3TV")
    assert props2["coffees_served"] > props1["coffees_served"]  # persisted + incremented
```

### Green gate for #4

- All existing tests pass + 2 new tests.
- Seasonal overlay visible in `run.py` output during sweeps months.

---

## IMPROVEMENT #5 — Night-Identity Blocks & Sweeps Grid Rotation (P2, medium)

> **HANDOFF.md (L85-86) admits: "Sun-Mon prime night-identity blocks & sweeps
> stunt rotation are stubbed."**

### Problem

`GRID` (`programming.py:29-57`) is a flat 24-slot table. `get_slot()`
(`programming.py:86-96`) is a pure wall-clock lookup. No Sunday prime-time
special block, no TGIF rotation, no sweeps stunt substitution.

### Solution

**`programming.py`:**

1. Add `SWEEPS_GRID` — a seasonal variant of GRID that swaps in stunt titles
   during sweeps months (Jul/Oct/Nov/Dec per `content.SEASONS`).
2. `get_slot()` consults `world.current_season()` (passed in) and returns the
   sweeps variant slot when in a sweeps month.
3. Add `_is_sweeps_month(month)` using `content.SEASONS` keys 7, 10, 11, 12.

### Acceptance criteria

```python
def test_sweeps_month_swaps_grid_slot():
    slot = programming.get_slot(datetime(2026, 10, 31, 20, 0), season={"month": 10})
    assert "Halloween" in slot.title or "Sweeps" in slot.title
```

### Green gate for #5

- All existing tests pass + 2 new tests.

---

## IMPROVEMENT #6 — Gag Tracking Fix (P3, trivial)

> **Already partially implemented as a side-effect of #1** (step 8 of the tick()
> rewrite calls `bump_gag` from `on_air`). This item is listed for completeness.

### Green gate for #6

- `bump_gag` has ≥2 callers in `tvn/` production code.
- `world_digest()["gags"]` returns counts > 0 after a run.
- `top_gags()` returns gags ordered by non-zero counts.

---

## IMPROVEMENT #7 — Lower-Third + Station ID Rendering (P3, trivial)

> **Already partially implemented as part of #2.** `draw_lower_third` and
> `draw_full("station_id")` are called in the updated `render_segment`.

---

## NON-GOALS (out of scope for this pass)

Per the constraint "No source changes" applies to the critic pass — these are
explicitly deferred:

| Item | Reason | FULL_VISION ref |
|------|--------|-----------------|
| LLM Gary layer (OpenRouter) | Honestly documented as future in HANDOFF.md:93; zero-cost fallback is green | FULL_VISION L74 |
| Real SPC player round-trip | Toolchain-blocked (no SPC player on PATH, `audio.py:152-161`); emulator-captured beds ship instead | FULL_VISION L43-44 |
| Real ROM-sprite replacement of procedural painter | Documented upgrade path; current sprites pass content gates honestly | FULL_VISION L37-39 |
| Actual Twitch live streaming | Requires stream key; A/V streaming code (`-stream`) is complete and tested via local MediaMTX | FULL_VISION L114-116 |

---

## ORDER OF EXECUTION

```
#1  Series Lifecycle Engine + Sweeps Wiring   (P0, ~8 tests)   ← START HERE
    ↓ must complete before #3, #5 (they depend on tick() creating pitch shows)
#2  Commercial Pod Rendering                   (P1, ~4 tests)   ← parallel-safe
#3  Night Shift Protocol                       (P1, ~3 tests)   ← depends on #1
#4  Set Evolution                              (P2, ~2 tests)   ← parallel-safe
#5  Night-Identity / Sweeps Grid               (P2, ~2 tests)   ← depends on #1
#6  Gag Tracking Fix                           (P3, ~1 test)    ← side-effect of #1
#7  Lower-Third + Station ID                   (P3, ~1 test)    ← side-effect of #2
```

## DONE BAR (the full set)

The broadcast is **genuinely LIVING** (not just running) when ALL of the
following are true after a `run.py --seconds 30` run on a persistent DB:

1. **Birth**: At least one new `Show(status="pitch")` exists that was created by
   `tick()` or `develop_pilots()` from an unresolved relationship arc.
2. **Growth**: At least one show advanced `pitch → pilot → series` during the run.
3. **Death**: At least one show transitioned `series → cancellation` (rating-gated).
4. **Afterlife**: At least one show transitioned `cancellation → revival → pilot`
   (only during a sweeps month).
5. **Career evolution**: At least one character's `career_level` changed from
   `"regular"` to `"star"` (or `"legend"`).
6. **Gags tracked**: At least one `RunningGag.occurrence_count > 0`.
7. **Sweeps stunt**: During a sweeps month, the morning report lists a sweeps
   stunt event in `recent_events`.
8. **Morning report auto-generated**: `OUTPUT/morning_reports/latest.json` exists
   and contains lifecycle transitions, not just decay.
9. **Commercial pod visible**: A 30-second MP4 contains commercial card frames
   (promo/national/local/PSA/station_id) and a lower-third overlay.
10. **All tests green**: ≥120 tests pass (113 existing + ≥7 new), `ffprobe`
    confirms a non-blank MP4 with aac audio + h264 video, A/V sync < 0.2s.

If any of 1-8 fails, the broadcast is still *running*, not *living*.
