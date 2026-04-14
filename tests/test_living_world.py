from app.living_world import (
    Character,
    Timeline,
    Session,
    generate_gossip,
    simulate_24hr,
    morning_report,
)
from app.characters import index_characters
import json


def test_table_insert_query():
    session = Session()
    char = Character(
        name="TestChar", game="TestGame", lore="TestLore", sprites="test.png"
    )
    session.add(char)
    session.commit()
    queried = session.query(Character).filter_by(name="TestChar").first()
    assert queried.name == "TestChar"
    session.delete(char)
    session.commit()


def test_gossip_gen():
    session = Session()
    index_characters()  # Ensure chars
    gossips = generate_gossip(session)
    assert len(gossips) >= 1
    session.close()


def test_24hr_sim():
    session = Session()
    before_events = len(session.query(Timeline).all())
    success = simulate_24hr(session)
    after_events = len(session.query(Timeline).all())
    assert success
    assert after_events - before_events >= 20
    session.close()


def test_morning_report():
    session = Session()
    report = morning_report(session)
    data = json.loads(report)
    assert "characters" in data
    session.close()


def test_integration_24hr_report():
    session = Session()
    simulate_24hr(session)
    report = morning_report(session)
    data = json.loads(report)
    assert len(data["recent_events"]) > 0
    assert "relationships" in data
    session.close()
