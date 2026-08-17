# CRITIQUE — T3MPLATE TV Network MVP (v0.9-stage7, commit 09765f4)

> **CRITIC pass — adversarial gate.** This is NOT a blessing. The brief was: tear
> into the gap between the shipped MVP and FULL_VISION.md, file precise citations
> for every claim, label each gap ABSENT / PARTIAL / BROKEN, and hand the BUILDER
> a precise, testable build scope. No source code was touched during this pass.
>
> **Method:** Every claim below is backed by a `file:line` citation from the actual
> source tree at commit `09765f4`. Where behavior is absent, the citation points to
> the function that *should* contain it but does not. Where code is dead (defined
> but unreachable), the citation shows the definition and the call-site search that
> proves zero callers.

---

## 1. WHAT THE MVP ACTUALLY DOES (verified, not flattering)

### The broadcast loop (`runner.py:127-189`, `run_forever`)

The 24/7 loop is `run_forever` (`runner.py:127`). In **record mode** it calls
`_record_cycle` once per pass (`runner.py:184`):

1. `_next_seed()` mints a per-airing seed (`runner.py:86-89`).
2. `programming.get_slot()` resolves the current 24h grid slot (`runner.py:113`).
3. `_decide_differing(g, slot, seed)` calls `gary.GaryPD.decide()` and retries up
   to 8 times if the dialogue signature collides with the last airing
   (`runner.py:92-108`). This is the real, live GAP-3 novelty guard — consecutive
   same-slot airings genuinely differ.
4. `world.on_air(cast, show, tension, genre)` applies causal feedback
   (`runner.py:115-117`).
5. `segment_frames(seg, seconds=dur)` renders frames (`runner.py:121`).
6. `segment_audio(seg, dur, variant=seed)` fetches audio keyed by `fmt:seconds:variant`
   (`runner.py:122`).
7. `output.write_video(frames, out, audio=a)` pipes to ffmpeg → MP4 chunk
   (`runner.py:123`).

In **stream mode** (`runner.py:142-178`) an inner `stream_av_forever` generator
decides once, renders all frames, then yields `(frame, pcm_chunk)` pairs locked
per-frame to `stream_rtmp` (`output.py:139`).

After each cycle, `_maybe_tick(world)` fires (`runner.py:186`).

### tick() — the maintenance pass (`world.py:557-579`)

`tick()` runs hourly via `_maybe_tick` (`runner.py:192-204`). On THIS commit it
does **exactly three things**:

| Line | What it does | Effective in production? |
|------|-------------|--------------------------|
| `world.py:561-562` | Decays every `Relationship.score` by `score * 0.98` | **YES** — the only lifecycle mutation that actually fires |
| `world.py:564-565` | `Show.status="pitch"` → `"cancellation"` | **NO — DEAD CODE** (see §2.1) |
| `world.py:566-575` | Cancelled show → host `career.seeking_work=True`, `employer=""`, show → `"syndication"` | **NO — DEAD CODE** (same root cause) |
| `world.py:576-578` | Gag decay: if `last_used` > 4 days ago, `count *= 0.8` | **TECHNICALLY YES but vacuous** (gags are never bumped, see §2.6) |

That is the **entire** tick(). There is no pilot phase, no rating gate, no
revival, no season check, no sweeps stunt, no career promotion.

### on_air() — the causal feedback (`world.py:461-546`)

This is the MVP's **genuine strength**. For every pair in the on-air cast:
- Builds a root `TimelineEvent` for the airing (`world.py:477-481`), chained via
  `caused_by_event_id` to form a causal DAG.
- Applies `_airing_delta` — a mean-reverting pull toward `±BASELINE` (65) with
  tension push (`world.py:432-450`), so pairs oscillate rather than ratchet to
  ±100.
- Adjusts each co-host's popularity via `_pop_delta` toward `_POP_BASELINE` (60)
  (`world.py:452-459`).
- Advances the Show: increments `airings`, `episode_count`, rotates
  `episode_title` from the genre pool, mean-reverts `rating` toward ~7.0
  (`world.py:519-545`). This IS wired in the live loop (production passes grid-slot
  titles, and `on_air` upserts them as real Shows — the F-3.1 fix).

The causal chain (reason + `caused_by_event_id`) is verified by
`test_stage3_living.py:122-143`.

### Seeding — `_seed` / `_seed_now` (`world.py:259-316`)

- `_seed()` (`world.py:260-273`) is idempotent and concurrency-safe (inserts iff
  `Character.count() == 0`, catches `IntegrityError`).
- `_seed_now()` (`world.py:275-316`) inserts the curated 9-character cast from
  `content.CAST` (`content.py:12-40`), friendship/feud pairs from
  `SEED_FRIENDSHIPS` / `SEED_FEUDS` (`content.py:44-46`), directed relationship
  arcs from `RELATIONSHIP_ARCS` (`world.py:65-72`), running gags
  (`world.py:302-307`), **and 6 Shows — all with `status="series"`**
  (`world.py:308-316`).
- Seeds 6 Careers — **all `career_level="regular"`, `employer="T3TV"`**
  (`world.py:297-301`). No intern, no star, no legend.
- Calls `_seed_season_state()` which persists the calendar-derived SeasonState
  row (`world.py:219-230`).

### Programming — the fixed 90s grid (`programming.py:27-57`)

A 24-slot `GRID` (sorted by `start_min`), each `Slot` carrying `daypart`, `title`,
`fmt`, `dur_min`. `get_slot(now)` returns the active slot (`programming.py:86-96`).
`build_pod()` builds a `promo → national×N → local×M → psa → station_id` pod
(`programming.py:113-141`). `build_handoff()` builds a hand-off (`programming.py:154-157`).

### Gary PD — the beat selector (`gary.py:59-313`)

`decide(slot, seed)` reads `world_digest()`, picks a beat via
`_choose_beat` (priority: seeking_work → feud → friendship → gag → ratings →
show_promo), fills dialogue templates from REAL world state, and returns a
`BroadcastSegment` (`gary.py:160-278`). `_choose_beat` respects
`content.FORMAT_ALLOWED_BEATS` (`content.py:153-168`) so infomercials/PSAs never
air feud content — verified by `test_stage3_living.py:34-46`.

### Renderer — what actually draws (`renderer.py:262-300`)

`render_segment()` yields: 20 bumper frames (`draw_bumper`) → N show-beat frames
(`frame()`) → 24 hand-off frames (static promo card). That is the **entire**
on-air render. `frame()` draws: background, cast (motion-driven), dialogue box,
rating badge, and **either** a scrolling ticker **or** a corner bug
(`renderer.py:214-243`).

**113 tests pass.** `run.py --seconds 12` produces a non-blank 512×448 h264+aac
MP4. The green gate is real for what it claims — but it claims very little.

---

## 2. GAP LIST — against FULL_VISION, ranked by leverage-to-effort

Citations resolve to the function that **should** implement the behavior but
either does not or does so only in dead code.

---

### 2.1 SERIES LIFECYCLE ENGINE — ABSENT (dead code)

**FULL_VISION §Show Lifecycle Engine** (`FULL_VISION.md:76-81`):
> Pitch → Pilot → Series → Syndication → Cancellation → Potential Revival
> Budget allocation per show affecting production values
> Cast changes when shows are cancelled (characters seek new work)
> Special events during sweeps weeks (crossovers, marathons, stunt casting)
> Retirement legends system for long-running characters

**What the code has:** A skeleton in `tick()` (`world.py:564-575`):
```python
for show in self.session.query(Show).filter_by(status="pitch").all():
    show.status = "cancellation"       # world.py:565
cancelled = self.session.query(Show).filter_by(status="cancellation").all()
for show in cancelled:                 # world.py:567
    for host in (show.hosts or []):
        career = ...filter(Character.name == host).first()
        if career:                     # world.py:570-573
            career.seeking_work = True
            career.employer = ""
    self.session.query(Show).filter_by(id=show.id).update(
        {"status": "syndication", "rating": show.rating})  # world.py:574-575
```

**What it does NOT have — and why the above is dead:**

| Gap | Evidence |
|-----|----------|
| **No pitch shows ever exist** — all seeded shows are `status="series"` (`world.py:312`); `on_air` upserts shows as `status="series"` (`world.py:528`). The `filter_by(status="pitch")` at `world.py:564` therefore matches **zero** shows in every production tick. | `world.py:312`, `world.py:528`, `world.py:564` |
| **No pilot phase** — `status` enum (`Show.status`, `world.py:129`) has no `"pilot"` value exercised in production. The only non-`series`/`pitch` value ever written is `"syndication"` (`world.py:574`). `active_shows()` (`world.py:358-361`) queries `status IN ("series", "syndication", "pilot")` — the `"pilot"` option is unreachable. | `world.py:129`, `world.py:360`, `world.py:574` |
| **No rating-driven syndication gate** — syndication is an unconditional `status` flip (`world.py:574-575`), not gated on `show.rating`. A show with rating 2.0 and a show with rating 9.0 both flip to `"syndication"` identically. | `world.py:574-575` |
| **No revocation/cancellation based on rating** — `on_air` evolves `show.rating` (`world.py:535`) but nothing ever reads that rating to decide cancellation. Ratings float mean-reverting toward 7.0 and never trigger a status change. | `world.py:534-535` |
| **No revival hook** — no code anywhere transitions a show from `"cancellation"`/`"syndication"` back to `"series"` or `"pilot"`. The `Show.status` column (`world.py:129`) has no path inward from cancellation. | `world.py:129` (no revival transition in any function) |
| **No budget field** — FULL_VISION §78 demands budget allocation. `Show` (`world.py:125-138`) has no `budget` column. No production-value scaling exists in `renderer.py` or `gary.py`. | `world.py:125-138` |
| **No retirement legend system** — FULL_VISION §81. No character retires, no legend status, no `career_level` promotion. | `world.py:119` (only value ever set: `"regular"`, `world.py:300`) |
| **No cast changes on cancellation** — the `career.seeking_work = True` path (`world.py:570-573`) would fire IF a show were cancelled, but no show is ever cancelled (dead-code root). And even if it did fire, it only sets a boolean — no character is moved to a new show. | `world.py:564-575` (unreachable) |
| **No sweeps/crossover special event** — `content.SEASONS` (`content.py:111-124`) marks Midsummer Sweeps (mo 7), Halloween Haunt (mo 10), Thanksgiving Sweeps (mo 11), Holiday Specials (mo 12). Nothing in `programming.get_slot()`, `gary.decide()`, `renderer.render_segment()`, or `world.tick()` reads `SeasonState` or `content.SEASONS` to trigger a stunt. | `content.py:111-124` (defined, unused) |

**Concrete test that would prove the gap:**
```python
def test_lifecycle_creates_pilot_then_series_or_cancellation(world):
    # Create a pitch show, run tick() enough times, assert it advances
    world.session.add(Show(name="Test Show", status="pitch", genre="news", rating=5.0))
    world.session.commit()
    world.tick()  # must advance pitch → pilot, not cancellation
    # → currently: pitch → cancellation directly (no pilot, no rating gate)
```

```python
def test_syndication_gated_on_rating(world):
    high = Show(name="Hit", status="series", genre="news", rating=9.0)
    low  = Show(name="Miss", status="series", genre="news", rating=2.0)
    for s in (high, low): world.session.add(s)
    world.session.commit()
    world.tick()
    # → currently: NEITHER transitions; tick() only touches "pitch" shows
```

---

### 2.2 SWEEPS STUNT PLANNING — ABSENT

**FULL_VISION** (`FULL_VISION.md:70`): Gary PD — "Sweeps week special events planning",
"Cross-show crossover planning during sweeps". (`FULL_VISION.md:80`):
"Special events during sweeps weeks (crossovers, marathons, stunt casting)".
(`FULL_VISION.md:183`): "Gary's sweeps week planning and special event coordination"
during Night Shift.

**What the code has:**
- `content.SEASONS` (`content.py:111-124`) — a calendar→(season, holiday) map with
  holiday entries that NAME sweeps: `"Midsummer Sweeps"` (7), `"Halloween Haunt"` (10),
  `"Thanksgiving Sweeps"` (11), `"Holiday Specials"` (12).
- `SeasonState` ORM (`world.py:141-150`) — persists season/holiday/month.
- `_seed_season_state()` (`world.py:219-230`) and `current_season()`
  (`world.py:236-257`) — persist and return the season dict.
- `current_season()` opportunistically sets `show.arc_label` to
  `f"{season} Sweeps Run"` (`world.py:249-255`) — **purely cosmetic text**.

**What it does NOT have — SeasonState is read-only flavor:**

| Gap | Evidence |
|-----|----------|
| `SeasonState` / `current_season()` is never read by `programming.py`, `gary.py`, `renderer.py`, or `runner.py`. | `grep -rn SeasonState\|current_season tvn/programming.py tvn/gary.py tvn/renderer.py tvn/runner.py` → **0 matches** |
| `get_slot()` (`programming.py:86-96`) never checks month/season/holiday. The `GRID` (`programming.py:29-57`) is a flat 24-slot table with no sweeps variant. | `programming.py:86-96` (no season check) |
| `build_pod()` (`programming.py:113-141`) never injects sweeps stunts, crossovers, or marathon blocks. Pod grammar is identical in July and January. | `programming.py:113-141` (no season-aware variant) |
| `gary.decide()` (`gary.py:160-278`) never consults `world_digest()["season"]` for stunt planning. Beat priority `_BEAT_PRIORITY` (`gary.py:53-54`) has no sweeps entry. | `gary.py:53-54`, `gary.py:160-278` (no season/stunt logic) |
| No crossover mechanics — `on_air()` (`world.py:461-546`) takes a single `cast` list; there is no cross-show guest injection, no "marathon" schedule block. | `world.py:461-546` |
| The one nod (`world.py:249-255` "Sweeps Run" arc_label) is string decoration — it does not change the schedule, the pod, the beat, or the rating threshold. | `world.py:251-255` |

**Concrete test that would prove the gap:**
```python
def test_sweeps_month_triggers_stunt_event():
    # Force December (Holiday Specials / Thanksgiving Sweeps carryover)
    world.tick(days=1)  # should consult SeasonState
    # → currently: tick() ignores season entirely
```

---

### 2.3 CAREER TRAJECTORY DEPTH — ABSENT

**FULL_VISION §Career Trajectories** (`FULL_VISION.md:62`):
"Intern → Regular → Star → Legend (with salary progression)".
**§Contract Negotiations** (`FULL_VISION.md:63`):
"Based on performance, popularity, and Gary's mood".

**What the code has:**
- `Career` ORM (`world.py:112-122`): `show_type`, `show_count`, `rating`,
  `career_level`, `employer`, `seeking_work`.
- Seeding (`world.py:297-301`): every character gets `career_level="regular"`,
  `employer="T3TV"`, `show_count=1`, `rating=6.0`.
- `seeking_work()` (`world.py:377-379`) / `world_digest()` (`world.py:373-395`)
  expose the list.
- `gary._choose_beat()` (`gary.py:126-129`) has a `seeking_work` beat that reads
  `digest["seeking_work"]`.

**What it does NOT have:**

| Gap | Evidence |
|-----|----------|
| `career_level` is set ONCE at seed (`world.py:300`) and NEVER updated. No function transitions regular→star→legend or reverses. | `world.py:300`; `grep career_level tvn/world.py` → 2 hits: the column def + the seed |
| `career.show_count` stays at 1 forever. `on_air()` (`world.py:461-546`) updates `show.rating` and `show.airings` but never `Career.show_count`. | `world.py:519-545` (no Career mutation) |
| `career.rating` stays at 6.0 forever. No contract negotiation adjusts it. | `world.py:300` |
| `employer` is set to `""` only inside the DEAD tick() branch (`world.py:573`). | `world.py:573` (unreachable) |
| `seeking_work` is set to `True` only inside the DEAD tick() branch (`world.py:572`). Since no show is ever cancelled, `digest["seeking_work"]` is ALWAYS EMPTY, and the `seeking_work` beat (`gary.py:126-129`) NEVER fires. | `world.py:564-575` (dead root) |
| No contract negotiation logic. `on_air()` evolves `show.rating` (`world.py:535`) and relationship scores but never touches Career fields. | `world.py:461-546` |
| Gary's `mood` (`gary.py:62`) and `_mood_for()` (`gary.py:155-157`) are computed but never influence career decisions. | `gary.py:62`, `gary.py:155-157` (unused output) |

**Concrete test that would prove the gap:**
```python
def test_career_evolves_from_regular_to_star(world):
    # Air a show 50+ times with high ratings, assert career_level rises
    for _ in range(50):
        world.on_air(["mario", "luigi"], show="News of T3TV", tension=0)
    c = world.session.query(Career).filter_by(character=...mario...).first()
    assert c.career_level == "star"  # → currently: always "regular"
```

```python
def test_seeking_work_beat_fires_when_cancelled(world):
    show = world.session.query(Show).first(); show.status = "pitch"
    world.session.commit(); world.tick()
    d = world.world_digest()
    assert d["seeking_work"]  # → currently: tick() cancel path is dead
```

---

### 2.4 SET EVOLUTION — ABSENT

**FULL_VISION §Set Evolution** (`FULL_VISION.md:60`):
"Weather, lighting, props change with story integrity and seasonal progression".
(`FULL_VISION.md:107-111`):
"Seasonal decorations (holiday themes, summer breaks)",
"Weather effects visible through windows (rain, snow, sunshine)",
"Set upgrades based on show performance and budget",
"Prop continuity (consistent coffee mugs, desk items, background details)".

**What the code has:**
- `assets._procedural_background(set_name)` (`assets.py:130-181`) draws static
  SNES-palette backgrounds per set.
- `assets.background(set_name)` (`assets.py:95-107`) prefers real captures but
  falls back to the procedural painter.

**What it does NOT have:**

| Gap | Evidence |
|-----|----------|
| No weather overlay. `renderer.draw_background()` (`renderer.py:63-65`) calls `assets.background(set_name)` with a static name. No rain/snow/sunshine effect exists. | `renderer.py:63-65` |
| No seasonal decoration. `current_season()` (`world.py:236-257`) persists season but `renderer.frame()` (`renderer.py:214-243`) and `draw_background()` never read it. | `world.py:236-257`, `renderer.py:214-243` (no season read) |
| No prop continuity. `renderer.frame()` draws a fresh background every frame (`renderer.py:218`). No persistent desk items, coffee mugs, or set dressing evolution. | `renderer.py:217-218` |
| No set upgrades based on performance. `Show.rating` (`world.py:535`) evolves but is never read by `renderer` or `assets` to upgrade a set. | `world.py:534-535` (rating written, never read for visuals) |

**Concrete test that would prove the gap:**
```python
def test_seasonal_decoration_changes_background():
    # Force month=10 (Halloween Haunt), render a frame, assert spooky overlay
    # → currently: draw_background ignores season; always same static set
```

---

### 2.5 NIGHT SHIFT PROTOCOL — ABSENT

**FULL_VISION §Night Shift Protocol** (`FULL_VISION.md:177-185`):
> During off-hours (2AM-5AM local time):
> - Autonomous show development using character relationships
> - New pilot pitches based on unresolved storylines or character arcs
> - Relationship evolution driven by off-screen interactions
> - Set evolution and seasonal preparation
> - Gary's sweeps week planning and special event coordination
> - Asset pipeline maintenance and verification
> - Morning report generation for creator review

**What the code has:**
- `_maybe_tick(world)` (`runner.py:192-204`) fires `world.tick()` once per hour via a
  monotonic timer — guaranteed to run regardless of start time (BUG-2 fix,
  verified by `test_stage4_balance.py:119-138`).

**What it does NOT have — Night Shift is just the same hourly decay:**

| Gap | Evidence |
|-----|----------|
| No time-gating to 2AM-5AM. `_maybe_tick` fires every 3600s regardless of clock time (`runner.py:203`). | `runner.py:192-203` |
| No autonomous show development. `tick()` (`world.py:557-579`) never creates new Shows or pilots based on "unresolved storylines." | `world.py:557-579` (only decay + dead cancel path) |
| No pilot pitching. No code path creates a `Show(status="pitch")` from a relationship arc or running gag. | (no creation path in `world.py`) |
| No off-screen relationship evolution. `tick()` only decays scores (`world.py:562`); no "off-screen interaction" model. | `world.py:561-562` |
| No morning report auto-generation. `morning_report()` (`world.py:582-598`) is called ONLY from `run.py` (`run.py:41`) — the one-shot demo. It is never scheduled during night shift. | `world.py:582-598`, `run.py:41` |
| No asset pipeline maintenance during off-hours. | (no such code) |

**Concrete test that would prove the gap:**
```python
def test_night_shift_2am_creates_pilot_from_storyline(world):
    # Force 2:30 AM, ensure relationships exist, run night_shift()
    # → currently: no such function; _maybe_tick just decays scores
```

---

### 2.6 GAG TRACKING — BROKEN (definition with zero callers)

**FULL_VISION** (`FULL_VISION.md:58`):
"Running Gag Tracker: Jokes, catchphrases, and running bits persist and evolve".

**What the code has:**
- `RunningGag` ORM (`world.py:153-159`): `gag_text`, `occurrence_count`, `last_used`.
- `bump_gag(gag_text)` (`world.py:548-555`): increments `occurrence_count`, notes a timeline event.
- Seeded with 4 gags at `occurrence_count=0` (`world.py:302-307`).
- `top_gags()` (`world.py:363-365`) queries by `occurrence_count DESC`.

**What it does NOT — bump_gag is never called:**

| Evidence |
|----------|
| `grep -rn "bump_gag" tvn/ --include="*.py" \| grep -v "def bump_gag"` → **0 matches** |
| `on_air()` (`world.py:461-546`) never calls `bump_gag`. |
| `gary.decide()` (`gary.py:160-278`) never calls `bump_gag`. |
| `runner.run_once()` / `_record_cycle()` / `run_forever()` never call `bump_gag`. |
| `world_digest()` returns `gags` with `count=0` for all entries (`world.py:363-365`). `top_gags()` orders by `occurrence_count` (all 0) — the ordering is effectively arbitrary. |

**Result:** The "Running Gag Tracker" exists as a fully designed data model that
never increments. Gags are seeded and decayed-but-never-incremented. The gag
beat in `gary.decide()` (`gary.py:132-133`) selects from `digest["gags"]` but
those gags sit at count 0 forever.

**Concrete test that would prove the gap:**
```python
def test_on_air_bumps_gag_occurrence(world):
    world.bump_gag("Yoshi eats everything")  # manual call works...
    g = world.top_gags()[0]
    assert g.occurrence_count >= 1  # ...but production never calls bump_gag
```

---

### 2.7 COMMERCIAL POD RENDERING — ABSENT (grammar without broadcast)

**FULL_VISION** (`FULL_VISION.md:95-101`):
"Authentic 90s-style ad blocks (90 seconds typical)", "Bumpers and station IDs
between shows", "Public service announcements".

**What the code has:**
- `PodElement` / `build_pod()` / `Pod grammar` (`programming.py:106-141`) —
  produces `promo → national×N → local×M → psa → station_id`.
- `HandOff` / `build_handoff()` (`programming.py:144-157`).
- `broadcast.BroadcastSegment` fields: `commercial`, `promo`, `psa`, `station_id`
  (`broadcast.py:39-49`).
- `renderer.draw_full()` (`renderer.py:204-211`) can render commercial/PSA cards.

**What it does NOT:**

| Evidence |
|----------|
| `render_segment()` (`renderer.py:262-300`) renders ONLY: bumper → show beats → hand-off promo. It NEVER calls `build_pod()`, NEVER iterates `PodElement`s, NEVER calls `draw_full("commercial")` or `draw_full("psa")`. |
| `gary.decide()` sets `commercial=slot.fmt in DAYPART_FORMATS["overnight"]` (`gary.py:277`) — a boolean flag. `renderer.render_segment` reads `segment.bumper`, `segment.beats`, `segment.hand_off`, `segment.ticker`, `segment.rating`, `segment.background`, `segment.cast` — but NEVER reads `segment.commercial`. | `gary.py:277` (set, never read) |
| `build_pod()` is called ONLY in `test_programming.py:28-34`. In production code (runner/gary/renderer), `build_pod` is **never imported or called**. | `grep -rn "build_pod" tvn/runner.py tvn/gary.py tvn/renderer.py` → **0 matches** |
| `draw_lower_third()` (`renderer.py:169-180`) is defined but never called in `frame()` or `render_segment()`. | `grep "draw_lower_third" renderer.py` → 1 match (def only) |
| `draw_full("station_id")` / `draw_full("color_bars")` (`renderer.py:204-211`) — defined, never called in the broadcast pipeline. | `grep "draw_full" renderer.py` → 2 matches (def + call inside `render_segment` only for promo) |
| Bumpers (`draw_bumper`, `renderer.py:196-202`) DO render, but only the 20-frame lead-in — no inter-show bumper, no station ID loop, no color bars. | `renderer.py:278-285` (only bumper lead-in) |

**Concrete test that would prove the gap:**
```python
def test_render_segment_includes_commercial_pod():
    seg = broadcast.BroadcastSegment(..., commercial=True)
    frames = list(renderer.render_segment(seg))
    # → currently: commercial flag is ignored; no pod frames rendered
```

---

### 2.8 NIGHT-IDENTITY BLOCKS & GRID FIDELITY — ABSENT

**FULL_VISION** (`FULL_VISION.md:84-94`): The 90s daily schedule with distinct
night-identity blocks (prime-time sitcom block, late-night talk, Sunday night movie
slots, etc.). Sweeps stunt rotation.

**What the code has:** A broad-brush 24-slot `GRID` (`programming.py:29-57`).

**Gap:** HANDOFF.md (`HANDOFF.md:85-86`) explicitly admits:
> "⚠️ Sun-Mun prime night-identity blocks & sweeps stunt rotation are stubbed
> (not wired into slot selection)."

`get_slot()` (`programming.py:86-96`) is a pure wall-clock lookup into `GRID`.
There is no Sunday-night special, no Must-See/MFN/TGIF block rotation, no sweeps
stunt substitution. `content.SEASONS` holiday markers are never consulted.

**Concrete test:**
```python
def test_sunday_prime_time_uses_sunday_block():
    # Sunday 8pm should trigger a special Sunday block per RESEARCH_90S
    # → currently: returns "The Super Mario Bros. Show" (sitcom) always
```

---

### 2.9 LOWER-THIRD NEVER DRAWN — BROKEN

**FULL_VISION** (`FULL_VISION.md:100`): "Bumpers and station IDs between shows".
The `Cast.title` field (`broadcast.py:22`) is populated by Gary
(`gary.py:180-181`: `title=meta["role"]`) with the character's on-air role.

**Gap:** `renderer.draw_lower_third()` (`renderer.py:169-180`) is DEFINED but
**never called**. `frame()` (`renderer.py:214-243`) draws background, cast,
dialogue, rating, bug/ticker — but **no name/title overlay** appears on any cast
member. The lower-third code exists for tests (see `test_regressions.py:217-227`
which only checks it doesn't raise) but is absent from the live render pipeline.

**Concrete test:**
```python
def test_frame_includes_lower_third():
    # Render a frame, assert pixel differences in the lower-left where
    # draw_lower_third would paint — currently: no lower-third pixels
```

---

### 2.10 LLM GARY LAYER — ABSENT (honestly documented as future)

**FULL_VISION** (`FULL_VISION.md:74`): "LLM Integration: Now powered by OpenRouter."
HANDOFF.md (`HANDOFF.md:93`): "LLM Gary layer on top of the (green) fallback."

**Gap:** `gary.py:8`: "No LLM API key required -- this is the zero-cost content
director." `decide()` (`gary.py:160-278`) uses only `world_digest()` + templates.
There is NO OpenRouter / LLM integration anywhere. This is honestly documented
as future work in `HANDOFF.md:93` and `RELEASE_NOTES:5`, but it is genuinely
absent.

**Honest status:** ABSENT — but honestly labeled, so not a deception gap.

---

## 3. HONEST STATUS SUMMARY

| # | Gap | FULL_VISION ref | Status | Why |
|---|-----|-----------------|--------|-----|
| 2.1 | Series Lifecycle Engine | §Show Lifecycle Engine (L76-81) | **ABSENT** | tick() has skeleton but no pitch shows ever exist; pitch→cancellation→syndication path is dead code (all shows seeded as `series`, `on_air` upserts as `series`). No pilot, no rating gate, no revival, no budget, no retirement. |
| 2.2 | Sweeps Stunt Planning | §Gary PD (L70), §Show Lifecycle (L80) | **ABSENT** | `content.SEASONS` defines sweeps holidays (L111-124) but `SeasonState` is read-only flavor — never consulted by `get_slot()`/`decide()`/`tick()`. `get_slot` is a pure wall-clock lookup. |
| 2.3 | Career Trajectory Depth | §Career Trajectories (L62), §Contract Negotiations (L63) | **ABSENT** | `career_level` set once to `"regular"` at seed (L300), never updated. `show_count`/`rating` never evolve. `seeking_work` only set in dead-code tick() branch. |
| 2.4 | Set Evolution | §Set Evolution (L60), Evolving Sets (L107-111) | **ABSENT** | `draw_background` uses static set; `current_season` never read by renderer; no weather/prop/set-upgrade rendering. |
| 2.5 | Night Shift Protocol | §Night Shift (L177-185) | **ABSENT** | `_maybe_tick` fires hourly (not 2AM-5AM gated); `tick()` only decays + dead cancel path; no show development, no pilot pitching, no morning report auto-gen. |
| 2.6 | Gag Tracking | §Running Gag Tracker (L58) | **BROKEN** | `bump_gag()` (L548) defined but NEVER called from production code. Gags stay at count=0. `top_gags()` orders by count (all 0) — arbitrary. |
| 2.7 | Commercial Pod Rendering | §Commercial Architecture (L95-101) | **ABSENT** | `build_pod()`/`build_handoff()` exist in `programming.py` but are never called from runner/gary/renderer. `render_segment` ignores `segment.commercial`. `draw_lower_third`/`draw_full` defined but unused in pipeline. |
| 2.8 | Night-Identity / Sweeps Grid Rotation | §90s Schedule (L84-94) | **ABSENT** | HANDOFF.md (L85-86) admits it. `GRID` is a flat table; no Sunday/prime sweeps block variants. |
| 2.9 | Lower-Third Overlay | §90s Chrome (L100) | **BROKEN** | `draw_lower_third()` (L169) defined, never called in `frame()`/`render_segment()`. |
| 2.10 | LLM Gary Layer | §LLM Integration (L74) | **ABSENT** | Honestly documented as future. No OpenRouter integration. |

### What the MVP genuinely does well (no bless, just facts)

- **Mean-reverting relationships** (`_airing_delta`, `world.py:432-450`): scores
  oscillate around ±65, never saturate. Verified by
  `test_stage4_balance.py:52-77`.
- **Causal event DAG** (`on_air`, `world.py:461-546`): every mutation carries a
  `reason` + `caused_by_event_id`. Verified by `test_stage3_living.py:122-156`.
- **Episode continuity on live grid titles** (`on_air` upsert, `world.py:519-545`):
  shows created from grid-slot titles advance `episode_count` + rotate titles.
  Verified by `test_stage5_motion.py:191-204`.
- **Per-airing audio+video novelty**: `_decide_differing` (`runner.py:92-108`) +
  `Mixer.track_for` variant key (`audio.py:213-233`). Verified by
  `test_stage7_av.py:15-30` and `test_stage3_living.py:85-117`.
- **A/V sync bound**: `_pad_audio_to_frames` + `_av_sync_ok` (`output.py:55-77`).
  Verified by `test_stage7_av.py:43-62`.

### What is overstated

- **Release notes** (`RELEASE_NOTES_v0.9-stage7.md:6`): "113 unit tests pass" —
  TRUE (verified: `python -m pytest → 113 passed`). But the release notes claim
  "on-air sprite animation" (`L71`) while the animation library only has 6 base
  motions (`animation.py:31-45`) and Bowser's custom `laugh`/`roar` + Yoshi's `hop`
  + Wario's `cackle` (`animation.py:96-107`) are registered but **never selected**
  by `gary._choose_beat` — beats only map to `talk`/`happy`/`walk`/`idle`
  (`content.py:205,231,251,298,322`). The custom motions exist in the library but
  are unreachable through the broadcast decision path.
- **Release notes** (`RELEASE_NOTES_v0.9-stage7.md:77`): "Full grid fidelity:
  night-identity blocks ... sweeps stunt rotation are stubbed" — this is honestly
  listed under "What's next," NOT claimed as done. GOOD — this is honest.
- **`FULL_VISION.md:59`**: "Show History: Complete lifecycle tracking from pitch
  to cancellation" — the Show ORM HAS a `status` column (`world.py:129`) with
  values pitch/cancellation/syndication, creating the **appearance** of a lifecycle,
  but the only lifecycle transition that fires in production is... none. The
  schema implies capability that the logic does not deliver.

---

## 4. BUILD SCOPE (precise — see `BUILD_SCOPE.md` for the detailed version)

### Highest-leverage single improvement: Series Lifecycle Engine + Sweeps Wiring

The broadcast currently **runs** (airs grid slots, advances episodes, drifts
relationships) but does not **live**. The single change that converts "running"
into "living" is: **make `tick()` actually drive show lifecycle events**, gated
by ratings and season, with sweeps stunts. Everything else (career evolution,
night-shift development, revival) hangs on this.

**Acceptance criteria (the DONE bar for this single improvement):**
- `tick()` creates pitch shows from unresolved storylines (relationship arcs + gags)
- pitch → pilot → series transitions based on pilot airing ratings
- series → syndication when `rating >= threshold`
- series → cancellation when `rating <= threshold`
- cancellation → revival when rating recovers AND season is a sweeps month
- `career_level` evolves: regular → star (show success) → legend (retirement)
- `seeking_work` characters actually appear as guests (unblocks dead-code beat)
- Sweeps months (Jul/Oct/Nov/Dec per `content.SEASONS`) trigger stunt events
- `morning_report()` generated automatically (not just one-shot)

**Green gate:** ≥113 tests still pass; new lifecycle tests pass; `run.py --seconds 12`
produces non-blank MP4 showing a pilot/syndication/cancellation event in the
morning report; `bump_gag` called from `on_air` (fixes gag tracking as a side
effect of wiring lifecycle to gags).

The full ordered, testable build plan is in **`BUILD_SCOPE.md`**.
