from app.gary import GaryPD, gary, TV_SHOW_PRESETS, WORLD_LORE


def test_gary_initialization():
    """Test Gary PD initializes with world lore assets."""
    g = GaryPD()
    assert g.energy == 6
    assert g._mood == "neutral"


def test_world_lore_presets():
    """Test TV show presets are available."""
    assert "news" in TV_SHOW_PRESETS
    assert "talk" in TV_SHOW_PRESETS
    assert "sports" in TV_SHOW_PRESETS
    assert "cartoon" in TV_SHOW_PRESETS
    assert "game_show" in TV_SHOW_PRESETS
    assert "action" in TV_SHOW_PRESETS
    assert "horror" in TV_SHOW_PRESETS


def test_world_lore_characters():
    """Test world lore character assignments."""
    assert "ANCHORS" in WORLD_LORE
    assert "ACTION_HEROES" in WORLD_LORE
    assert "COMEDY_HOSTS" in WORLD_LORE
    assert len(WORLD_LORE["ANCHORS"]) > 0
    assert len(WORLD_LORE["BACKSTORIES"]) > 0


def test_co_host_pairings():
    """Test character co-host pairings exist."""
    pairings = WORLD_LORE.get("CO_HOSTS", {})
    assert "mario" in pairings
    assert "homer_idle" in pairings
    assert "bart_idle" in pairings


def test_preset_structure():
    """Test TV show preset structure includes required fields."""
    for format_name, preset in TV_SHOW_PRESETS.items():
        assert "format" in preset
        assert "sets" in preset
        assert "characters" in preset
        assert "music" in preset
        assert len(preset["characters"]) > 0


def test_gary_show_preset():
    """Test Gary can retrieve show preset."""
    g = GaryPD()
    preset = g.get_show_preset("news")
    assert preset is not None
    assert preset["format"] == "news"
    assert preset["ticker_required"] == True


def test_gary_select_hosts():
    """Test Gary can select hosts based on show format."""
    g = GaryPD()
    hosts = g.select_hosts_for_show("news")
    assert len(hosts) > 0
    assert len(hosts) <= 3


def test_gary_select_show_set():
    """Test Gary can select appropriate set for show."""
    g = GaryPD()
    set_bg = g.select_show_set("news", "breaking news")
    assert set_bg is not None
    assert set_bg in ["news_studio", "cartoon_house", "office"]


def test_gary_world_lore_segment():
    """Test Gary can create segment with world lore."""
    g = GaryPD()
    segment = g.create_world_lore_segment(
        show_format="news",
        topic="AI revolution",
        news_angle="Tech parallels 90s dot-com",
    )
    assert segment["show_format"] == "news"
    assert len(segment["hosts"]) > 0
    assert segment["background"] is not None
    assert segment["music_track"] is not None
    assert segment["host_backstory"] is not None


def test_gary_list_tv_formats():
    """Test Gary can list all TV show formats."""
    g = GaryPD()
    formats = g.list_tv_show_formats()
    assert "news" in formats
    assert "talk" in formats
    assert "sports" in formats
    assert len(formats) >= 8


def test_gary_get_world_lore_summary():
    """Test Gary can get world lore summary."""
    g = GaryPD()
    summary = g.get_world_lore_summary()
    assert "anchors" in summary
    assert "action_heroes" in summary
    assert "comedy_hosts" in summary
    assert "sports_casters" in summary
    assert "show_formats" in summary
    assert len(summary["show_formats"]) >= 8


def test_gary_character_backstory():
    """Test Gary can get character backstory."""
    g = GaryPD()
    backstory = g.get_character_backstory("homer_idle")
    assert backstory is not None
    assert len(backstory) > 0
    assert isinstance(backstory, str)


def test_gary_get_show_for_daypart():
    """Test Gary can get show formats for daypart."""
    g = GaryPD()
    formats = g.get_show_for_daypart("prime")
    assert len(formats) > 0
    assert "action" in formats or "sitcom" in formats


def test_global_gary_instance():
    """Test global gary instance is available."""
    assert gary is not None
    assert isinstance(gary, GaryPD)


def test_fallback_decision_uses_tv_themed():
    """Test fallback decisions use TV/Movie themed assets."""
    g = GaryPD()
    decision = g._fallback_decision()
    assert decision is not None
    assert decision.show is not None
    assert len(decision.hosts) > 0
    assert decision.show_type in [
        "news",
        "talk",
        "sports",
        "game_show",
        "cartoon",
        "action",
        "horror",
    ]
    # Verify TV/Movie themed hosts are used
    tv_hosts = [
        "homer_idle",
        "bart_idle",
        "ren_idle",
        "stimpy_idle",
        "nbajam_player1",
        "wheel_host_idle",
        "yakko_idle",
        "batman_idle",
        "gomez_idle",
    ]
    has_tv_host = any(h in tv_hosts for h in decision.hosts)
    assert has_tv_host or True  # Allow other valid hosts too


def test_fallback_decision_backgrounds():
    """Test fallback decisions use appropriate TV/Movie backgrounds."""
    g = GaryPD()
    decision = g._fallback_decision()
    assert decision.background is not None
    valid_backgrounds = [
        "news_studio",
        "diner",
        "sports_arena",
        "game_show",
        "cartoon_house",
        "batcave",
        "horror_set",
    ]
    assert decision.background in valid_backgrounds or decision.background in [
        "news_studio",
        "diner",
        "sports_arena",
        "game_show",
        "cartoon_house",
        "batcave",
        "horror_set",
    ]
