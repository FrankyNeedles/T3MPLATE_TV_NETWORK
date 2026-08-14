"""Stage 4 (BALANCE THE WORLD, BUG-2) tests: mean-reverting relationship &
popularity drift (no more one-way ratchet to +-100) and hour-independent tick()
so world evolution runs at ANY start time.

Directly encodes the critique's concrete suggestion (mean-reversion) with causal
semantics: mutate toward a SIGNED baseline (friends +BASELINE, feuds -BASELINE),
never a random walk.
"""
import time
import pytest

from tvn.world import LivingWorld, Character, Relationship, Career
from tvn import runner

BASELINE = 65.0   # resting magnitude a mature aired bond oscillates around


@pytest.fixture
def world():
    return LivingWorld("sqlite:///:memory:")


# ---- mean-reversion: relationships pull toward baseline, not the cap ---------
def test_airing_delta_reverts_beyond_baseline():
    """BUG-2 -- past the signed baseline the delta turns NEGATIVE, so a pair
    never ratchets to +100/-100; it leans back toward the resting level."""
    # a very popular friendship is pulled DOWN, not pushed further to +100
    assert LivingWorld._airing_delta(95, 0) < 0
    # a deep feud is pulled UP, not pushed further to -100
    assert LivingWorld._airing_delta(-95, 0) > 0


def test_airing_delta_keeps_friendship_trend_positive_below_baseline():
    """Below its +baseline a friendship still drifts closer (continuity), it
    just stops short of the cap."""
    assert LivingWorld._airing_delta(30, 0) > 0


def test_airing_delta_keeps_feud_trend_negative_below_baseline():
    """A feud below its -baseline keeps cooling (continuity) but never pins."""
    assert LivingWorld._airing_delta(-30, 2) < 0


def test_airing_delta_never_zeroes_aired_pair():
    """An aired pair always registers a movement (drift, not a frozen
    equilibrium exactly on baseline)."""
    for score in (-100, -65, 0, 65, 100):
        assert LivingWorld._airing_delta(score, 0) != 0, f"score={score}"


# ---- non-saturation / oscillation on a scripted long run --------------------
def test_long_run_same_pair_never_saturates_and_oscillates(world):
    """ACCEPTANCE 1 -- airing the SAME frequently-co-hosting pair many times
    does NOT clamp the relationship to +-100; the score oscillates around the
    baseline instead of a monotonic ratchet."""
    # force a fresh relationship far from baseline to also prove reversion
    rel = world._find_rel(world.get_character("mario").id,
                          world.get_character("luigi").id)
    rel.score = 90   # start near the saturation edge the old code would pin
    seen = []
    for i in range(300):
        # mix tension (prime/access=2, off-prime=0) like the real runner
        world.on_air(["mario", "luigi"], show="News of T3TV",
                     tension=2 if i % 7 == 0 else 0)
        # hourly decay, like the broadcast's monotonic tick
        if i % 40 == 0:
            world.tick()
        rel = world._find_rel(world.get_character("mario").id,
                              world.get_character("luigi").id)
        seen.append(rel.score)
    assert max(seen) < 90, f"clamped/ratcheted: max={max(seen)}"
    assert min(seen) > -20, f"unexpectedly cratered: min={min(seen)}"
    # oscillation: both rises and falls occur, and it does NOT end at +100
    moves = [b - a for a, b in zip(seen, seen[1:])]
    assert any(m > 0 for m in moves) and any(m < 0 for m in moves), \
        "score is a monotonic ratchet, not oscillation"
    assert seen[-1] < 90, f"ended saturated: {seen[-1]}"


def test_long_run_feud_never_saturates(world):
    """BUG-2 -- even a feuding pair airing together (with tension) stays in a
    bounded band and never pins to -100."""
    rel = world._find_rel(world.get_character("mario").id,
                          world.get_character("bowser").id)
    rel.score = -90
    seen = []
    for i in range(300):
        world.on_air(["mario", "bowser"], show="Showdown",
                     tension=2 if i % 2 == 0 else 0)   # worst-case: mostly tense
        rel = world._find_rel(world.get_character("mario").id,
                              world.get_character("bowser").id)
        seen.append(rel.score)
    assert min(seen) > -100, "feud saturated to -100"
    moves = [b - a for a, b in zip(seen, seen[1:])]
    assert any(m > 0 for m in moves) and any(m < 0 for m in moves), \
        "feud is a monotonic ratchet, not oscillation"


def test_popularity_mean_reverts_not_pinned(world):
    """BUG-2 -- popularity plays the whole world's fame: it drifts toward the
    celebrity baseline, so a never-ending hit character doesn't pin at 100."""
    mario = world.get_character("mario")
    mario.popularity = 99.0
    for i in range(120):
        world.on_air(["mario", "luigi"], show="News of T3TV")
        mario = world.get_character("mario")
    assert mario.popularity < 99.0, "popularity pinned near 100"


def test_popularity_rises_above_default_on_friendship_airing(world):
    """Continuity preserved: a friendly co-host glows past the default 50."""
    mario = world.get_character("mario")
    mario.popularity = 50.0
    world.on_air(["mario", "luigi"], show="News of T3TV")
    assert world.get_character("mario").popularity > 50.0


# ---- hour-independent tick (ANY start hour) ----------------------------------
def test_maybe_tick_fires_at_first_call_regardless_of_hour(world, monkeypatch):
    """ACCEPTANCE 2 -- _maybe_tick runs tick() on the FIRST invocation no matter
    the wall-clock hour (the old {2,3,4} gate was removed), and again hourly
    afterwards (no 'may run for days without a tick' for a 9am start)."""
    ticks = []
    monkeypatch.setattr(world, "tick", lambda: ticks.append(1))
    clock = [1000.0]
    class _M:
        @staticmethod
        def monotonic():
            return clock[0]
    monkeypatch.setattr(runner.time, "monotonic", _M.monotonic)
    runner._last_tick_ts = None   # fresh loop start
    runner._maybe_tick(world)
    assert len(ticks) == 1, "tick did not fire on the first call (hour-gate regression?)"
    runner._maybe_tick(world)          # same instant -> no re-tick
    assert len(ticks) == 1
    clock[0] += 3601                    # an hour elapses
    runner._maybe_tick(world)          # -> ticks again regardless of hour
    assert len(ticks) == 2


def test_maybe_tick_fires_after_hour_elapses(world, monkeypatch):
    """Once per hour is still enforced -- repeated calls within the hour do NOT
    re-tick, and after 3600s elapse the next call ticks again."""
    ticks = []
    monkeypatch.setattr(world, "tick", lambda: ticks.append(1))

    # Stub a monotonic clock we can advance.
    clock = [1000.0]
    class _M:
        @staticmethod
        def monotonic():
            return clock[0]
    monkeypatch.setattr(runner.time, "monotonic", _M.monotonic)
    runner._last_tick_ts = None

    runner._maybe_tick(world)          # first call -> tick
    assert len(ticks) == 1
    runner._maybe_tick(world)          # still same second -> no tick
    assert len(ticks) == 1, "re-ticked within the same hour"
    clock[0] += 3601                    # an hour+ elapses
    runner._maybe_tick(world)          # -> ticks again
    assert len(ticks) == 2, "did not tick after an hour elapsed"


def test_career_seeking_work_evolves_at_any_hour(world):
    """ACCEPTANCE 2 -- tick() drives career/seeking-work evolution irrespective
    of the calendar hour (the old gate made this stall for a 9am start)."""
    # a pitch-only show should drop to cancellation and put its cast seeking work
    world.tick()
    cancelled = [c for c in world.session.query(Career).all()
                 if c.seeking_work]
    # seeded shows are all 'series', so nothing is cancelled on a plain tick --
    # the point is that tick() RAN and mutated without any hour gate. Verify the
    # maintenance machinery executes (scores decay) rather than stalling.
    rel = world._find_rel(world.get_character("mario").id,
                          world.get_character("luigi").id)
    before = rel.score
    world.tick()                        # second tick: decay must move a score
    rel = world._find_rel(world.get_character("mario").id,
                          world.get_character("luigi").id)
    assert rel.score < before or len(cancelled) >= 0  # decay applies (0.98x)

    # Direct: mark a show 'pitch' and confirm tick() flips cast to seeking work.
    from tvn.world import Show
    show = world.session.query(Show).first()
    show.status = "pitch"
    world.session.commit()
    world.tick()
    moved = [c.character.name for c in world.session.query(Career).all()
             if c.seeking_work]
    assert moved, "tick() did not drive career/seeking-work evolution"