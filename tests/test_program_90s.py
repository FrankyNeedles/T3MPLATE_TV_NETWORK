"""
Tests for 90s TV Programming Engine.
"""

from datetime import datetime
from app.program_90s import (
    TVProgrammingEngine,
    Daypart,
    DialogueBubble,
    MusicCue,
    SFXCue,
    create_talking_bubble,
    create_music_cue,
    create_stinger_sfx,
)


class TestDaypartDetection:
    """Test 90s daypart detection."""

    def test_morning_daypart(self):
        engine = TVProgrammingEngine()
        assert engine.get_current_daypart() in Daypart

    def test_sweeps_period(self):
        engine = TVProgrammingEngine()
        sweeps = engine.get_sweeps_period()
        # Should return None unless Feb, May, or Nov
        month = datetime.now().month
        if month in [2, 5, 11]:
            assert sweeps is not None
        else:
            assert sweeps is None


class TestTalkingBubbles:
    """Test SNES dialogue bubbles."""

    def test_create_round_bubble(self):
        bubble = create_talking_bubble("mario", "It's-a me!", "round")
        assert bubble.character == "mario"
        assert bubble.text == "It's-a me!"
        assert bubble.bubble_type == "round"
        assert bubble.duration_frames == 90

    def test_create_shout_bubble(self):
        bubble = create_talking_bubble("ryu", "HADOUKEN!", "shout")
        assert bubble.bubble_type == "shout"
        assert bubble.duration_frames == 90

    def test_create_thought_bubble(self):
        bubble = create_talking_bubble("ness", "I sense something...", "thought")
        assert bubble.bubble_type == "thought"

    def test_bubble_to_command(self):
        bubble = DialogueBubble("mario", "Hi!", "round")
        cmd = bubble.to_gary_command()
        assert "BUBBLE" in cmd
        assert "mario" in cmd
        assert "Hi!" in cmd


class TestMusicCues:
    """Test SNES music cues."""

    def test_create_music_cue(self):
        cue = create_music_cue("smw_bowser", "SUPER MARIOWORLD", 90.0)
        assert cue.track_name == "smw_bowser"
        assert cue.game == "SUPER MARIOWORLD"
        assert cue.duration == 90.0
        assert cue.loop is True

    def test_create_stinger_cue(self):
        cue = create_music_cue("sf2_vs", "Street Fighter 2", 10.0, stinger=True)
        assert cue.stinger is True
        assert cue.duration == 10.0

    def test_cue_to_command(self):
        cue = MusicCue("smw_title", "SUPER MARIOWORLD", 30.0)
        cmd = cue.to_gary_command()
        assert "MUSIC" in cmd
        assert "smw_title" in cmd


class TestSFXCues:
    """Test sound effect cues."""

    def test_create_sfx_cue(self):
        sfx = create_stinger_sfx("smw_jump", "SUPER MARIOWORLD", 5.0)
        assert sfx.sfx_name == "smw_jump"
        assert sfx.trigger_time == 5.0
        assert sfx.volume == 1.0

    def test_sfx_to_command(self):
        sfx = SFXCue("smw_coin", "SUPER MARIOWORLD", 3.0)
        cmd = sfx.to_gary_command()
        assert "SFX" in cmd
        assert "smw_coin" in cmd


class TestProgrammingStrategy:
    """Test 90s programming strategy."""

    def test_get_programming_strategy(self):
        engine = TVProgrammingEngine()
        strategy = engine.get_programming_strategy()

        assert "daypart" in strategy
        assert "sweeps_mode" in strategy
        assert "scene_length_optimal" in strategy
        assert "commercial_interval_min" in strategy

    def test_scene_length_by_daypart(self):
        engine = TVProgrammingEngine()

        sitcom_length = engine.calculate_optimal_scene_length("sitcom", Daypart.PRIME)
        assert sitcom_length == 120.0  # 2 min for sitcoms in prime

        soap_length = engine.calculate_optimal_scene_length(
            "soap_opera", Daypart.DAYTIME
        )
        assert soap_length == 60.0  # 1 min for soaps in daytime


class TestSegmentMusic:
    """Test music selection for segments."""

    def test_get_segment_music(self):
        engine = TVProgrammingEngine()

        cold_open_music = engine.SEGMENT_MUSIC.get("cold_open", [])
        assert len(cold_open_music) > 0
        assert cold_open_music[0][0] == "smw_title"

    def test_dramatic_mood_music(self):
        engine = TVProgrammingEngine()

        dramatic_music = engine.SEGMENT_MUSIC.get("act_three", [])
        assert any("bowser" in track or "mk" in track for track, _ in dramatic_music)


class TestSFXSelection:
    """Test SFX selection for dramatic moments."""

    def test_get_comedic_sfx(self):
        engine = TVProgrammingEngine()

        comedic_sfx = engine.DRAMATIC_SFX.get("comedic", [])
        assert len(comedic_sfx) > 0

    def test_get_dramatic_sfx(self):
        engine = TVProgrammingEngine()

        dramatic_sfx = engine.DRAMATIC_SFX.get("dramatic", [])
        assert any("mk" in sfx or "bowser" in sfx for sfx, _ in dramatic_sfx)


class TestRatingsContext:
    """Test Nielsen ratings context."""

    def test_sweeps_detection(self):
        engine = TVProgrammingEngine()
        ratings = engine.get_ratings_context()

        month = datetime.now().month
        if month in [2, 5, 11]:
            assert ratings.sweeps_period is not None
        else:
            assert ratings.sweeps_period is None

    def test_ratings_context_fields(self):
        engine = TVProgrammingEngine()
        ratings = engine.get_ratings_context()

        # Verify essential fields exist
        assert hasattr(ratings, "sweeps_period")
        assert hasattr(ratings, "is_premiere")
        assert hasattr(ratings, "is_finale")
        assert hasattr(ratings, "holiday_special")
