#!/usr/bin/env python3
"""
Living World Tests
Unit and integration tests for persistence and simulation.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.living_world import LivingWorld
from app.characters import load_characters_from_assets


@pytest.fixture
def temp_living_world():
    """Temporary DB for tests."""
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    lw = LivingWorld()
    lw.engine = engine
    lw.Session = Session
    lw.session = Session()
    yield lw
    lw.session.close()


def test_load_characters(temp_living_world):
    """Test character loading."""
    chars = load_characters_from_assets()
    assert len(chars) >= 3  # Minimum from sample
    assert "Mario" in [c["name"] for c in chars]


def test_create_relationship(temp_living_world):
    """Test relationship creation."""
    rel = temp_living_world.create_relationship(1, 2, 50)
    assert rel.score == 50
    # Update
    new_score = temp_living_world.update_relationship(
        "Mario", "Luigi", 10, "Hosted show"
    )
    assert new_score == 60


def test_simulate_day(temp_living_world):
    """Test day simulation."""
    sample_shows = [{"hosts": ["Mario", "Bowser"], "type": "news"}]
    report = temp_living_world.simulate_day(sample_shows)
    assert "new_relationships" in report
    assert len(report["gossip_generated"]) == 1


def test_morning_report(temp_living_world):
    """Test report generation."""
    report = temp_living_world.generate_morning_report()
    assert "Total Characters" in report
    assert "Gossip of the Day" in report


def test_career_entry(temp_living_world):
    """Test career creation."""
    career = temp_living_world.create_career_entry("Mario", "news", 8.5)
    assert career.rating == 8.5
    assert career.show_type == "news"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
