"""Living-world continuity engine tests."""
import pytest

from tvn.world import LivingWorld, Character


@pytest.fixture
def world():
    return LivingWorld("sqlite:///:memory:")


def test_seeded_curated_cast(world):
    assert world.session.query(Character).count() == 9
    names = [c.name for c in world.session.query(Character).all()]
    assert "mario" in names and "bowser" in names and "peach" in names


def test_world_digest_is_world_caused(world):
    d = world.world_digest()
    # the seeded feud (mario~bowser) must surface as content, not randomness
    feud_names = {(f["a"], f["b"]) for f in d["feuds"]}
    assert ("mario", "bowser") in feud_names or ("bowser", "mario") in feud_names
    assert d["gags"] and any("Yoshi" in g["gag"] or "Luigi" in g["gag"] for g in d["gags"])


def test_on_air_causal_delta(world):
    before = world._find_rel(world.get_character("mario").id,
                             world.get_character("luigi").id).score
    world.on_air(["mario", "luigi"], show="News of T3TV", tension=0)
    after = world._find_rel(world.get_character("mario").id,
                            world.get_character("luigi").id).score
    assert after != before  # co-hosting caused a relationship delta
    assert world.get_character("mario").popularity > 50.0


def test_on_air_feud_drifts_negative(world):
    rel = world._find_rel(world.get_character("mario").id,
                          world.get_character("bowser").id)
    before = rel.score
    world.on_air(["mario", "bowser"], show="Showdown", tension=2)
    after = world._find_rel(world.get_character("mario").id,
                            world.get_character("bowser").id).score
    assert after < before  # feuding co-stars drift further apart (continuity)


def test_bump_gag(world):
    world.bump_gag("Yoshi eats everything")
    g = [g for g in world.top_gags() if g.gag_text == "Yoshi eats everything"][0]
    assert g.occurrence_count == 1


def test_tick_and_seeking_work(world):
    world.tick()
    rep = world.morning_report()
    assert isinstance(rep["recent_events"], list)
    assert rep["stats"]["shows"] >= 6


def test_migration_rebuilds_stale_schema(tmp_path):
    """A stale old-schema DB (no 'kind' column) must be rebuilt, not crash."""
    db = tmp_path / "stale.db"
    from sqlalchemy import create_engine, text
    eng = create_engine(f"sqlite:///{db}")
    with eng.begin() as conn:
        conn.execute(text("CREATE TABLE characters (id INTEGER PRIMARY KEY, name VARCHAR)"))
    eng.dispose()
    w = LivingWorld(f"sqlite:///{db}")
    assert w.session.query(Character).count() == 9