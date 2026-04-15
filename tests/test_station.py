import pytest

try:
    import pygame
except ImportError:
    pygame = None

from app.station import Station


def test_station_init():
    """Test Station initialization."""
    station = Station()
    assert station.gary is not None
    assert station.living_world is not None
    assert station.tick_count == 0
    assert station.status["ready"] is True


def test_station_tick():
    """Test station tick increments counter."""
    station = Station()
    station.running = True
    initial_tick = station.tick_count
    station.tick()
    assert station.tick_count == initial_tick + 1


def test_station_daypart():
    """Test daypart detection."""
    station = Station()
    assert station._get_daypart(7.0) == "morning"
    assert station._get_daypart(12.0) == "daytime"
    assert station._get_daypart(18.0) == "evening"
    assert station._get_daypart(21.0) == "primetime"
    assert station._get_daypart(0.0) == "late"


def test_station_status():
    """Test station status tracking."""
    station = Station()
    status = station.tick()
    assert "shows" in status
    assert "relationships" in status
    assert "phase" in status


def test_emergency_fallbacks():
    """Test emergency fallback patterns."""
    from app.station import EmergencyFallbacks

    pattern = EmergencyFallbacks.test_pattern()
    assert pattern["type"] == "test_pattern"
    assert "colors" in pattern

    color_bar = EmergencyFallbacks.color_bar()
    assert color_bar["type"] == "color_bar"

    station_id = EmergencyFallbacks.station_id()
    assert station_id["type"] == "station_id"
    assert station_id["loop"] is True


if __name__ == "__main__":
    pytest.main(["-v", __file__])
