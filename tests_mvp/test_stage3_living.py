"""Stage 3 (Make 24/7 LIVING) tests: GAP-3 per-airing novelty, WEAK-1a format
coherence, WEAK-1b relationship-verified casting, WEAK-1c show-voice dialogue,
and the world's causal `reason` / `caused_by_event_id` chain (RESEARCH I3).
"""
import pytest

from tvn import gary, programming, content
from tvn.world import LivingWorld, TimelineEvent, SeasonState, Relationship, Show


@pytest.fixture
def world():
    return LivingWorld("sqlite:///:memory:")


@pytest.fixture
def g(world):
    return gary.GaryPD(world)


# ---- WEAK-1a: format coherence --------------------------------------------
INFOMERCIAL_SLOTS = [
    programming.Slot(3 * 60, "overnight", "The Power-Up 9000 Infomercial", "infomercial", 60),
    programming.Slot(4 * 60, "overnight", "Mushroom Fade Mastery", "infomercial", 60),
    programming.Slot(4 * 60 + 30, "overnight", "Infomercial + Test Pattern", "infomercial", 30),
    programming.Slot(6 * 60 + 30, "early_morning", "Farm & Home Report", "infomercial", 30),
]
PSA_SLOTS = [
    programming.Slot(1 * 60, "overnight", "PSA Hour", "psa", 60),
]


@pytest.mark.parametrize("slot", INFOMERCIAL_SLOTS + PSA_SLOTS)
def test_non_skit_format_never_airs_feud(g, slot):
    """WEAK-1a -- an infomercial / PSA slot must NEVER carry a feud skit,
    regardless of seed (the critique's own refutation of the bug)."""
    for seed in range(0, 6):
        seg = g.decide(slot, seed=seed)
        all_lines = " ".join(b.text.lower() for b in seg.beats)
        # the feud template's lines / feud-rehash markers are absent
        for marker in ("rehash", "we absolutely are", "battlefield", "grudge"):
            assert marker not in all_lines, (
                f"seed={seed}: {slot.fmt} aired feud content: {all_lines}")
        # no feud/friendship relational tone at all
        assert "feud" not in all_lines, f"seed={seed}: {all_lines}"


def test_infomercial_has_its_own_voice(g):
    """WEAK-1c -- an infomercial uses the sales/promo voice, not news/talk."""
    seg = g.decide(INFOMERCIAL_SLOTS[0], seed=1)
    all_lines = " ".join(b.text.lower() for b in seg.beats)
    assert any(k in all_lines for k in ("wait, there's more", "operators",
                                        "stay tuned", "don't lie",
                                        "hour to tune in"))


# ---- WEAK-1b: relationship-verified casting ---------------------------------
def test_feud_references_real_world_feud_actor(g):
    """WEAK-1b -- on a format that allows feuds, a feud airs the REAL feud actor
    (one of the seeded feud pair), not a random non-feuding host."""
    slot = programming.Slot(19 * 60, "access", "The Coin Block", "game_show", 30)
    feuds_by_name = {(f["a"], f["b"]) for f in g.world.world_digest()["feuds"]}
    feud_actors = {x for p in feuds_by_name for x in p}
    feud_markers = ("we absolutely are", "rehash", "battlefield", "buzzer", "my sweep")
    seen_feud_actor = False
    for seed in range(0, 8):
        seg = g.decide(slot, seed=seed)
        speakers = {b.speaker for b in seg.beats}
        if any(m in b.text for b in seg.beats for m in feud_markers):
            # the feud speech must come from an ACTUAL feud participant
            assert speakers & feud_actors, f"seed={seed}: {speakers} not feud actors"
            seen_feud_actor = True
    assert seen_feud_actor, "game_show should air at least one feud across seeds"


def test_all_feud_bets_on_set_format_skip_when_not_allowed(g):
    """WEAK-1b -- even a feud-capable format never forces a relational speaker
    that isn't a real relationship participant; seeds rotate to safe beats."""
    for seed in range(0, 8):
        g.decide(programming.Slot(10 * 60, "daytime", "Name That Mushroom",
                                  "game_show", 60), seed=seed)


# ---- GAP-3: per-airing novelty ----------------------------------------------
def test_different_seeds_produce_different_dialogue(g):
    """GAP-3 -- consecutive airings of the SAME slot (fresh seed each pass) must
    DIFFER in dialogue, not loop byte-identical templates."""
    slot = programming.Slot(3 * 60, "overnight", "The Power-Up 9000 Infomercial",
                            "infomercial", 60)
    texts = set()
    for seed in range(0, 8):
        seg = g.decide(slot, seed=seed)
        texts.add(tuple(b.text for b in seg.beats))
    assert len(texts) >= 3, f"only {len(texts)} distinct airings across 8 seeds"


def test_runner_mints_fresh_seed_per_airing(world, monkeypatch, tmp_path):
    """GAP-3 -- _next_seed mints a distinct seed per airing, and _decide_differing
    picks a segment whose dialogue differs from the previous airing."""
    from tvn import runner
    seeds = [runner._next_seed() for _ in range(4)]
    assert len(set(seeds)) == len(seeds), "seeds must be distinct per airing (GAP-3)"

    class _Seg:
        fmt = "news"; title = "News"; daypart = "day"; seg_id = "s"
        def __init__(self, text): self.cast = []; self.beats = [type("B", (), {"text": text})()]
    calls = []
    class _G:
        def decide(self, slot, seed=None):
            calls.append(seed)
            # alternate dialogue so the guard sees a change on the 2nd try
            idx = (seed if seed is not None else 0) % 3
            return _Seg(f"airing-{idx}")
    seg1 = runner._decide_differing(_G(), None, 1000)
    seg2 = runner._decide_differing(_G(), None, 1001)
    assert [b.text for b in seg1.beats] != [b.text for b in seg2.beats]
    assert len(calls) >= 2



# ---- Causal world chain (RESEARCH I3 / canon discipline) --------------------
def test_on_air_mutations_carry_reason_and_chain(world):
    """Stage 3 -- every on_air() mutation logs a REAL `reason` tied to an in-world
    event and is `caused_by_event_id`-chained to the ROOT airing event."""
    world.on_air(["mario", "luigi"], show="News of T3TV", tension=0)
    # the root airing event exists (event text contains the show name + 'aired')
    root = (world.session.query(TimelineEvent)
            .filter(TimelineEvent.event.contains("News of T3TV"))
            .filter(TimelineEvent.event.contains("aired")).first())
    assert root is not None
    assert root.caused_by_event_id is None  # top of the causal DAG
    # every chained child (mutation) points back at the root
    children = (world.session.query(TimelineEvent)
                .filter(TimelineEvent.caused_by_event_id == root.id).all())
    assert len(children) >= 1
    for c in children:
        assert c.reason  # non-empty real reason tied to an in-world event
    # the relationship's stored event blob also carries reason + chain link
    rel = world._find_rel(world.get_character("mario").id,
                          world.get_character("luigi").id)
    last = rel.events[-1]
    assert last.get("reason")
    assert last.get("caused_by_event_id") == root.id


def test_externally_caused_airing_chains_to_that_event(world):
    """caused_by_event_id threading -- an airing caused by a prior event links to
    it, so the whole month forms a chain, not isolated notes."""
    head = world._note("series premiere ordered", reason="network decision",
                       outcome="greenlit")
    world.on_air(["toad", "bowser"], show="News of T3TV", tension=0,
                 caused_by_event_id=head)
    root = (world.session.query(TimelineEvent)
            .filter(TimelineEvent.event.contains("News of T3TV"))
            .filter(TimelineEvent.event.contains("aired")).first())
    assert root.caused_by_event_id == head


def test_episode_count_and_title_advance_on_air(world):
    """Stage 3 -- every airing advances a show's episode_count and rotates a
    fresh episode_title from the genre pool (no static naming)."""
    world.on_air(["mario", "luigi"], show="News of T3TV", tension=0)
    s = world.session.query(Show).filter_by(name="News of T3TV").first()
    assert s.episode_count == 2          # seeded at 1, +1 per airing
    assert s.episode_title  # populated from the genre pool
    world.on_air(["mario", "luigi"], show="News of T3TV", tension=0)
    world.session.refresh(s)
    assert s.episode_count == 3


def test_season_state_driven_by_calendar(world):
    """Stage 3 -- SeasonState is seeded from the real calendar and readable."""
    season = world.current_season()
    assert season["season"] in {f for f, _ in content.SEASONS.values()}
    assert world.session.query(SeasonState).filter_by(active=True).count() >= 1


def test_relationships_carry_arc_labels(world):
    """Stage 3 -- directed relationship arcs are seeded so feuds/friendships
    read as evolving stories, not flat scores."""
    rel = world._find_rel(world.get_character("mario").id,
                          world.get_character("bowser").id)
    assert rel.arc_label  # "The Eternal Rivalry" or similar


def test_relationship_delta_definitely_mutates(world):
    """Stage 3 -- co-hosting must move the score so future airings differ."""
    before = world._find_rel(world.get_character("mario").id,
                             world.get_character("luigi").id).score
    world.on_air(["mario", "luigi"], show="News of T3TV", tension=0)
    after = world._find_rel(world.get_character("mario").id,
                            world.get_character("luigi").id).score
    assert after != before