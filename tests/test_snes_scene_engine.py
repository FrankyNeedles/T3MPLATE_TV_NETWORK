"""
Tests for SNES Scene Engine - Gary's programmatic scene creation interface.
"""

from pathlib import Path
from app.snes_scene_engine import (
    SNESSceneEngine,
    SceneDirector,
    GameSceneLibrary,
    SNESScene,
    SpriteReference,
    AudioReference,
    BackgroundReference,
)


class TestSNESSceneEngine:
    """Test the core scene engine."""

    def test_engine_singleton(self):
        """Test that engine is a proper singleton."""
        engine1 = SNESSceneEngine.get_instance()
        engine2 = SNESSceneEngine.get_instance()
        assert engine1 is engine2

    def test_list_available_games(self):
        """Test listing available games."""
        engine = SNESSceneEngine.get_instance()
        games = engine.list_available_games()
        assert len(games) > 0
        assert "SUPER MARIOWORLD" in games
        assert "THE LEGEND OF ZELDA" in games

    def test_list_available_characters(self):
        """Test listing available characters."""
        engine = SNESSceneEngine.get_instance()
        chars = engine.list_available_characters()
        assert len(chars) > 0
        assert "mario_idle" in chars
        assert "link_idle" in chars
        assert "fox_idle" in chars

    def test_list_available_tracks(self):
        """Test listing available music tracks."""
        engine = SNESSceneEngine.get_instance()
        tracks = engine.list_available_tracks()
        assert len(tracks) > 0
        assert "smw_bowser" in tracks
        assert "sf2_vs" in tracks

    def test_get_sprite_reference(self):
        """Test getting sprite reference for a character."""
        engine = SNESSceneEngine.get_instance()
        ref = engine.get_sprite_reference("mario_idle")
        assert isinstance(ref, SpriteReference)
        assert ref.character == "mario_idle"
        assert ref.game == "SUPER MARIOWORLD"
        assert ref.bank > 0

    def test_get_audio_reference(self):
        """Test getting audio reference for a track."""
        engine = SNESSceneEngine.get_instance()
        ref = engine.get_audio_reference("smw_jump")
        assert isinstance(ref, AudioReference)
        assert ref.track_name == "smw_jump"
        assert ref.audio_type == "sfx"

    def test_get_background_reference(self):
        """Test getting background reference for a genre."""
        engine = SNESSceneEngine.get_instance()
        ref = engine.get_background_reference("castle")
        assert isinstance(ref, BackgroundReference)
        assert ref.genre == "castle"

    def test_gary_prompt_generation(self):
        """Test that Gary prompt is generated properly."""
        engine = SNESSceneEngine.get_instance()
        prompt = engine.get_gary_prompt()
        assert "GARY" in prompt
        assert "SUPER MARIOWORLD" in prompt
        assert "create_scene" in prompt


class TestSceneDirector:
    """Test the Scene Director."""

    def test_create_scene_from_template(self):
        """Test creating a scene from a template."""
        engine = SNESSceneEngine.get_instance()
        director = SceneDirector(engine)

        scene = director.create_scene("SUPER MARIOWORLD", "castle_confrontation")
        assert isinstance(scene, SNESScene)
        assert scene.game == "SUPER MARIOWORLD"
        assert scene.scene_type == "castle_confrontation"
        assert len(scene.elements) > 0

    def test_create_custom_scene(self):
        """Test creating a custom scene."""
        engine = SNESSceneEngine.get_instance()
        director = SceneDirector(engine)

        scene = director.create_custom_scene(
            game="STREET FIGHTER 2",
            characters=["ryu_idle", "ken_idle"],
            background="city",
            music="sf2_vs",
        )
        assert isinstance(scene, SNESScene)
        assert scene.game == "STREET FIGHTER 2"

        # Verify characters were added
        char_elements = [e for e in scene.elements if e.element_type == "character"]
        assert len(char_elements) == 2

        # Verify music was set
        assert scene.music is not None
        assert scene.music.track_name == "sf2_vs"

    def test_describe_scene_for_gary(self):
        """Test scene description generation."""
        engine = SNESSceneEngine.get_instance()
        director = SceneDirector(engine)

        scene = director.create_scene("EarthBound", "boss_encounter")
        desc = director.describe_scene_for_gary(scene)

        assert "ness" in desc.lower()
        assert "boss_encounter" in desc


class TestSNESScene:
    """Test the SNESScene dataclass."""

    def test_add_character(self):
        """Test adding a character to a scene."""
        engine = SNESSceneEngine.get_instance()
        scene = SNESScene(
            scene_id="test_scene", scene_type="test", game="SUPER MARIOWORLD"
        )

        element = scene.add_character("mario_idle", pose="jump", position=(100, 150))
        assert element.name == "mario_idle"
        assert element.animation == "jump"
        assert element.position == (100, 150)
        assert len(scene.elements) == 1

    def test_set_background(self):
        """Test setting a background."""
        engine = SNESSceneEngine.get_instance()
        scene = SNESScene(
            scene_id="test_scene", scene_type="test", game="SUPER MARIOWORLD"
        )

        element = scene.set_background("forest")
        assert element.name == "forest"
        assert element.layer == 0
        assert scene.elements[0] == element

    def test_play_music(self):
        """Test setting music."""
        engine = SNESSceneEngine.get_instance()
        scene = SNESScene(
            scene_id="test_scene", scene_type="test", game="SUPER MARIOWORLD"
        )

        scene.play_music("smw_grass")
        assert scene.music is not None
        assert scene.music.track_name == "smw_grass"

    def test_add_sfx(self):
        """Test adding sound effects."""
        engine = SNESSceneEngine.get_instance()
        scene = SNESScene(
            scene_id="test_scene", scene_type="test", game="SUPER MARIOWORLD"
        )

        element = scene.add_sfx("smw_coin", time=2.5)
        assert element.name == "smw_coin"
        assert element.trigger_time == 2.5
        assert element.element_type == "sfx"

    def test_to_gary_script(self):
        """Test Gary script generation."""
        scene = SNESScene(
            scene_id="test_scene", scene_type="test_type", game="SUPER MARIOWORLD"
        )
        scene.add_character("mario_idle", pose="idle")
        scene.play_music("smw_grass")

        script = scene.to_gary_script()
        assert "# SCENE: test_scene" in script
        assert "# TYPE: test_type" in script
        assert "# GAME: SUPER MARIOWORLD" in script
        assert "CHARACTER(mario_idle" in script
        assert "MUSIC(smw_grass)" in script
        assert "# END_SCENE" in script

    def test_to_api_call(self):
        """Test API call generation."""
        scene = SNESScene(
            scene_id="test_scene", scene_type="test_type", game="SUPER MARIOWORLD"
        )
        scene.add_character("fox_idle", pose="fly")

        api_call = scene.to_api_call()
        assert api_call["scene_id"] == "test_scene"
        assert len(api_call["characters"]) == 1
        assert api_call["characters"][0]["name"] == "fox_idle"


class TestGameSceneLibrary:
    """Test the Game Scene Library."""

    def test_get_template(self):
        """Test getting a scene template."""
        template = GameSceneLibrary.get_template(
            "SUPER MARIOWORLD", "castle_confrontation"
        )
        assert template is not None
        assert "elements" in template
        assert "music" in template

    def test_list_scenes_for_game(self):
        """Test listing scenes for a game."""
        scenes = GameSceneLibrary.list_scenes_for_game("SUPER MARIOWORLD")
        assert len(scenes) > 0
        assert "castle_confrontation" in scenes
        assert "overworld_meadow" in scenes

    def test_list_all_games(self):
        """Test listing all games with templates."""
        games = GameSceneLibrary.list_all_games()
        assert len(games) > 0
        assert "SUPER MARIOWORLD" in games
        assert "THE LEGEND OF ZELDA" in games
        assert "STREET FIGHTER 2" in games


class TestFULLVISIONCompliance:
    """Test FULL_VISION.md compliance for scene creation."""

    def test_uses_real_rom_assets(self):
        """Verify scene creation uses real ROM asset references."""
        engine = SNESSceneEngine.get_instance()
        ref = engine.get_sprite_reference("mario_idle")

        # Verify the reference contains real ROM data
        assert ref.rom_hash is not None
        assert len(ref.rom_hash) == 64  # SHA-256 hash length
        assert ref.rom_path is not None
        assert Path(ref.rom_path).exists() or "ROM_SOURCE" in ref.rom_path

    def test_scene_has_provenance(self):
        """Verify scenes maintain asset provenance."""
        scene = SNESScene(scene_id="test", scene_type="test", game="SUPER MARIOWORLD")
        scene.add_character("luigi_idle")

        element = scene.elements[0]
        assert element.reference.rom_hash is not None
        assert element.reference.game in ["SUPER MARIOWORLD", "SUPER MARIOWORLD"]

    def test_traceable_asset_commands(self):
        """Verify scene elements have traceable Gary commands."""
        scene = SNESScene(scene_id="test", scene_type="test", game="SUPER MARIOWORLD")
        scene.add_character("link_idle")

        element = scene.elements[0]
        command = element.reference.to_gary_command()

        # Verify command format is traceable
        assert "SPRITE:" in command
        assert "@" in command
        assert "bank=" in command
        assert "offset=" in command
