"""BUILD_SCOPE #1 -- Series Lifecycle Engine + Sweeps Wiring.

These tests drive the full show lifecycle through `tick()` and `on_air()`:
pitch -> pilot -> series -> syndication/cancellation -> sweeps revival, plus the
career evolution and gag-tracking side effects. Before this change tick() was
dead code (no show was ever seeded 'pitch', so the pitch filter matched zero
rows); these tests prove the lifecycle now actually BIRTHS and KILLS shows.
"""
import pytest

from tvn import content
from tvn.world import Career, LivingWorld, RunningGag, Show


@pytest.fixture
def world():
    return LivingWorld("sqlite:///:memory:")


def _set_month(monkeypatch, month: int):
    """Point tvn.world's calendar at a fixed month so sweeps gates are testable
    regardless of the real wall-clock date."""
    from datetime import datetime as _dt

    class _FakeDT:
        _month = month

        @classmethod
        def now(cls):
            # naive datetime keeps tick()'s gag-aging arithmetic (now - last_used)
            # type-safe (the codebase's DTZ style is the established baseline).
            return _dt(2026, cls._month, 5, hour=3)  # noqa: DTZ001 - mirrors codebase

        @classmethod
        def fromisoformat(cls, *a):
            return _dt.fromisoformat(*a)

    monkeypatch.setattr("tvn.world.datetime", _FakeDT)


# --- 1. Pitch shows are BORN from strong unresolved storylines ---------------
def test_tick_creates_pitch_show_from_storyline(world):
    """A strong relationship arc with no active show spawns a pitch show."""
    rel = world._find_rel(world.get_character("mario").id,
                          world.get_character("bowser").id)
    rel.score = -80
    world.session.commit()
    shows_before = world.session.query(Show).count()
    world.tick()
    assert world.session.query(Show).count() > shows_before
    new_show = world.session.query(Show).filter_by(status="pitch").first()
    assert new_show is not None


# --- 2. Pitch -> pilot (never pitch -> cancellation directly) ----------------
def test_pitch_to_pilot_transition(world):
    """tick() advances pitch -> pilot (never pitch -> cancellation directly)."""
    world.session.add(Show(name="Test Pitch", status="pitch", genre="news", rating=6.0))
    world.session.commit()
    world.tick()
    s = world.session.query(Show).filter_by(name="Test Pitch").first()
    assert s.status in ("pilot", "series")  # NOT "cancellation"


# --- 3. Syndication gated on rating + episode count --------------------------
def test_syndication_gated_on_rating(world):
    high = Show(name="Hit", status="series", genre="news", rating=9.0,
                episode_count=15, airings=15)
    low = Show(name="Miss", status="series", genre="news", rating=2.0,
               episode_count=8, airings=8)
    for s in (high, low):
        world.session.add(s)
    world.session.commit()
    world.tick()
    assert world.session.query(Show).filter_by(name="Hit", status="syndication").first()
    assert world.session.query(Show).filter_by(name="Miss", status="cancellation").first()


# --- 4. Cancellation revives ONLY in a sweeps month --------------------------
def test_cancellation_revives_only_in_sweeps(world, monkeypatch):
    show = Show(name="Revivable", status="cancellation", genre="news",
                rating=8.0, episode_count=5)
    world.session.add(show)
    world.session.commit()

    # Non-sweeps month (Spring) -> stays cancelled.
    _set_month(monkeypatch, 3)
    world.tick()
    assert (world.session.query(Show)
            .filter_by(name="Revivable").first().status == "cancellation")

    # Sweeps month (Halloween Haunt, 10) -> revives to pilot.
    _set_month(monkeypatch, 10)
    world.tick()
    assert (world.session.query(Show)
            .filter_by(name="Revivable").first().status == "pilot")


# --- 5. Career promotes regular -> star on a strong show --------------------
def test_career_promotes_regular_to_star(world):
    mario = world.get_character("mario")
    before = world.session.query(Career).filter_by(character_id=mario.id).first()
    assert before.career_level == "regular"

    # Give the show a high rating so the on_air career gate promotes its host.
    s = world.session.query(Show).filter_by(name="News of T3TV").first()
    s.rating = 9.0
    world.session.commit()
    world.on_air(["mario", "luigi"], show="News of T3TV", tension=0)

    after = world.session.query(Career).filter_by(character_id=mario.id).first()
    assert after.career_level in ("star", "legend")
    assert after.show_count >= 2          # one per airing (+ seeded 1)


# --- 6. Gag occurrence increments on-air (bump_gag had ZERO callers) ---------
def test_gag_occurrence_increments_on_air(world):
    world.on_air(["yoshi", "toad"], show="Super Playhouse", tension=0, genre="cartoon")
    g = world.session.query(RunningGag).filter_by(gag_text="Yoshi eats everything").first()
    assert g.occurrence_count >= 1


# --- 7. Seeking-work fires when a show is CANCELLED --------------------------
def test_cancelled_show_cast_seeks_work(world):
    # yoshi/zelda host no seeded live show, so a cancellation leaves them truly
    # out of work (a host who ALSO has a live series would correctly stay employed).
    canceled = Show(name="Doomed", status="series", genre="news", rating=3.0,
                    hosts=["yoshi", "zelda"], episode_count=2, airings=2)
    world.session.add(canceled)
    world.session.commit()
    world.tick()
    seeking = world.seeking_work()
    assert "yoshi" in seeking and "zelda" in seeking


# --- 8. Sweeps stunt content + pod injection ---------------------------------
def test_sweeps_stunts_defined_for_each_sweeps_month():
    assert set(content.SWEEPS_STUNTS.keys()) == {7, 10, 11, 12}
    for month, titles in content.SWEEPS_STUNTS.items():
        assert titles, f"month {month} has no stunt titles"


def test_build_pod_injects_stunt_promo_in_sweeps(world):
    from tvn.programming import build_pod

    sweeps_pod = build_pod("prime", next_show="News", seed=1, season=10)
    assert any("SWEEPS STUNT" in e.text for e in sweeps_pod)
    # no stunt in a non-sweeps month
    normal_pod = build_pod("prime", next_show="News", seed=1, season=3)
    assert not any("SWEEPS STUNT" in e.text for e in normal_pod)


# --- 9. Gary picks a stunt beat during a sweeps month ------------------------
def test_gary_airs_stunt_beat_in_sweeps(world, monkeypatch):
    from tvn.gary import GaryPD
    from tvn.programming import Slot

    slot = Slot(start_min=19 * 60, daypart="prime", title="Talk of T3TV",
                fmt="talk", dur_min=30)
    _set_month(monkeypatch, 10)          # Halloween Haunt = sweeps
    seg = GaryPD(world).decide(slot, seed=7)
    assert any("stunt" in (b.text or "").lower() or
               "SWEEPS" in (b.text or "") for b in seg.beats), \
        "no stunt beat aired during sweeps"

# --- 10. Full pilot -> series promotion (airings + rating window) ------------
def test_pilot_promotes_to_series_after_pilot_window(world):
    """A pilot only earns a series order after its minimum 3-airing window AND
    a sustaining rating (>= 6.5); a strong pilot that hits the window promotes."""
    p = world.session.query(Show).filter_by(status="pilot").first()
    if p is None:
        p = Show(name="Test Pilot to Series", status="pilot", genre="news",
                 rating=6.8, airings=2, episode_count=2, hosts=["mario", "luigi"])
        world.session.add(p)
        world.session.commit()
    # below the window -> still a pilot
    world.tick()
    still = world.session.query(Show).filter_by(name=p.name).first()
    assert still.status in ("pilot", "series")   # never jumps to weak states
    # air enough to clear the 3-airing pilot window, then tick promotes
    still.airings = 3
    world.session.commit()
    world.tick()
    promoted = world.session.query(Show).filter_by(name=p.name).first()
    assert promoted.status == "series"


# --- 11. Career star -> legend retirement (rating >= 9.0 + star) -------------
def test_career_legend_retires_star(world):
    """A STAR who sustains a 9.0+ show retires as a LEGEND: kept in history but
    removed from the active cast pool."""
    wario = world.get_character("wario")
    career = world.session.query(Career).filter_by(character_id=wario.id).first()
    career.career_level = "star"
    s = world.session.query(Show).filter_by(name="Late_Night of T3TV").first()
    s.rating = 9.5
    world.session.commit()
    world.on_air(["wario"], show="Late_Night of T3TV", tension=0)
    career = world.session.query(Career).filter_by(character_id=wario.id).first()
    assert career.career_level == "legend"
    assert career.retired is True
