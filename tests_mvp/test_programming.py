"""Programming (fixed 90s grid + pod grammar) tests."""
from datetime import datetime
import pytest

from tvn import programming


def test_grid_covers_24h():
    assert programming.GRID[0].start_min == 0
    minutes = {s.start_min for s in programming.GRID}
    # slots all day, no gap beyond next slot start
    assert len(minutes) >= 20


def test_clock_maps_to_expected_slot():
    # 7:00pm = The Coin Block (access), 8pm prime sitcom, 6pm early news
    assert programming.get_slot(datetime(2026, 8, 13, 19, 10)).fmt == "game_show"
    assert programming.get_slot(datetime(2026, 8, 13, 20, 30)).fmt == "sitcom"
    assert programming.get_slot(datetime(2026, 8, 13, 18, 5)).fmt == "news"


def test_daypart_labels():
    assert programming.get_current_daypart(datetime(2026, 8, 13, 21, 0)) == "prime"
    assert programming.get_current_daypart(datetime(2026, 8, 13, 7, 30)) == "morning"
    assert programming.get_current_daypart(datetime(2026, 8, 13, 3, 0)) == "overnight"


def test_pod_grammar_order():
    """A pod is an ordered sequence: promo -> national -> local -> station id."""
    pod = programming.build_pod("prime", next_show="Chrono", seed=1)
    kinds = [p.kind for p in pod]
    assert kinds[0] == "promo"
    assert kinds[-1] == "station_id"
    assert "national" in kinds and "local" in kinds


def test_pod_local_heavy_in_news():
    pod_news = programming.build_pod("early_news", seed=2)
    pod_prime = programming.build_pod("prime", seed=2)
    n_local_news = sum(1 for p in pod_news if p.kind == "local")
    n_local_prime = sum(1 for p in pod_prime if p.kind == "local")
    assert n_local_news >= n_local_prime


def test_handoff_links_show_to_next():
    h = programming.build_handoff("News at 11", "The Late Show with Wario")
    assert h.to_show == "The Late Show with Wario"
    assert "Late Show" in h.next_tease


def test_next_slot_rounds():
    s = programming.Slot(23 * 60 + 35, "late_night", "The Late Show with Wario",
                         "late_night", 25)
    nxt = programming.next_slot(s)
    assert nxt.start_min == 0 or nxt == programming.GRID[0]