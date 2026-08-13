"""Gary PD / decision engine tests."""
import pytest

from tvn.world import LivingWorld
from tvn import gary, programming, content


@pytest.fixture
def g():
    return gary.GaryPD(LivingWorld("sqlite:///:memory:"))


def test_garry_decision_model_restored():
    """The deleted `class GaryDecision` (autopsy root cause) must exist again."""
    assert hasattr(gary, "GaryDecision")
    rec = gary.GaryDecision(show="News", show_type="news", hosts=["mario"])
    assert rec.show == "News" and rec.tv_rating == "TV-PG"


def test_decide_returns_renderable_segment(g):
    seg = g.decide(programming.get_slot())
    assert seg.cast and seg.beats
    assert all(c.kind in content.SPRITE_KIND for c in seg.cast)


def test_dialogue_has_no_unresolved_placeholders(g):
    """No {c1}/{c2} leaks -- content must be concrete, authored text."""
    for slot in [programming.get_slot(),
                 programming.Slot(7 * 60, "morning", "Mushroom Morning", "morning", 120),
                 programming.Slot(19 * 60, "access", "The Coin Block", "game_show", 30)]:
        seg = g.decide(slot)
        for b in seg.beats:
            assert "{" not in b.text, f"unresolved placeholder in: {b.text}"
            assert b.speaker not in ("{c1}", "{c2}", "{host}")


def test_beat_caused_by_world_feud(g):
    """Top seed feud (mario~bowser) should drive dialogue, not random filler."""
    seg = g.decide(programming.Slot(19 * 60, "access", "The Coin Block", "game_show", 30))
    all_lines = " ".join(b.text for b in seg.beats)
    d = g.world.world_digest()
    if d["feuds"]:
        assert "bowser" in all_lines or d["feuds"][0]["b"] in all_lines


def test_make_decision_is_valid_record(g):
    d = g.make_decision(programming.get_slot())
    assert d.topic and d.mood and d.dialogue


def test_choreograph_movement_library(g):
    seg = g.decide(programming.get_slot())
    moves = g.choreograph(seg)
    assert set(moves) == {c.name for c in seg.cast}
    for m in moves.values():
        assert m in ("idle", "talk", "happy", "wave", "walk", "jump", "attack")

    # movement library: unknown MOTION falls back to idle (never crashes feed)
        from tvn.animation import library
        poses, fps, loop = library.play("nonexistent_character", "no_such_motion")
        assert poses == ("idle",)