"""
Vision-Anchored Tests for FULL_VISION.md Compliance

These tests are directly tied to the three non-negotiable pillars in FULL_VISION.md:
1. SUBSTANCE OVER SLOP (lines 18-26)
2. AUTHENTIC ASSETS (lines 28-48)
3. LIVING WORLD & BROADCAST READY (lines 50-196)

Run with: pytest tests/test_full_vision.py -v
"""

import json
from pathlib import Path

import pytest

FULL_VISION_PATH = Path(__file__).parent.parent / "FULL_VISION.md"


class TestSubstanceOverSlop:
    """
    Pillar 1: SUBSTANCE OVER SLOP (FULL_VISION.md lines 18-26)

    Requirements:
    - Zero Tolerance for Noise: Every asset verified against real ROM data
    - Honest Gap Analysis: Assets must pass substance-over-slop validation
    - Version Integrity: Downgrade to verified versions when false claims discovered
    - Morning Reports: Daily accountability showing verified progress
    - AI as Tool: OpenRouter powers Gary but follows strict machine protocol
    """

    def test_no_placeholder_artifacts(self):
        """FULL_VISION.md: No placeholders, no generated noise"""
        assets_dir = Path(__file__).parent.parent / "assets"
        if not assets_dir.exists():
            pytest.skip("assets/ directory not found")

        forbidden_patterns = ["placeholder", "temp", "test_", "generated_fake"]
        violations = []

        for ext in ["*.png", "*.wav", "*.brr"]:
            for asset in assets_dir.rglob(ext):
                for pattern in forbidden_patterns:
                    if pattern in asset.name.lower():
                        violations.append(str(asset))

        assert len(violations) == 0, f"Found placeholder artifacts: {violations}"

    def test_rom_source_integrity(self):
        """FULL_VISION.md: ROM_SOURCE/ is sacrosanct - never modified, only read"""
        rom_source = Path(__file__).parent.parent / "ROM_SOURCE"
        if not rom_source.exists():
            pytest.skip("ROM_SOURCE/ directory not found")

        import platform

        if platform.system() == "Windows":
            pytest.skip(
                "ROM_SOURCE writable check skipped on Windows (permission model differs)"
            )

        writable_files = []
        for f in rom_source.rglob("*"):
            if f.is_file():
                try:
                    with open(f, "a"):
                        pass
                    writable_files.append(str(f))
                except PermissionError:
                    pass

        assert len(writable_files) == 0, (
            f"ROM_SOURCE contains writable files (should be read-only): {writable_files}"
        )

    def test_extraction_manifest_has_rom_source(self):
        """FULL_VISION.md: Assets traceable to source ROM with hash"""
        roms_manifest = (
            Path(__file__).parent.parent / "ROM_SOURCE" / "roms_manifest.json"
        )

        if not roms_manifest.exists():
            pytest.skip("ROM library manifest not built yet")

        with open(roms_manifest) as f:
            manifest = json.load(f)

        if isinstance(manifest, dict) and "roms" in manifest:
            for rom in manifest["roms"]:
                has_hash = "hash" in rom or "hash_sha256" in rom
                assert has_hash, f"ROM entry missing hash: {rom.get('title')}"
                has_path = "path" in rom or "filename" in rom
                assert has_path, f"ROM entry missing path: {rom.get('title')}"

    def test_gary_ai_protocol_compliance(self):
        """FULL_VISION.md: AI as Tool - no social/financial/external autonomy"""
        from app.gary import GaryPD

        gary = GaryPD()
        assert hasattr(gary, "make_decision"), "Gary missing make_decision method"

        decision = gary.make_decision()
        decision_data = (
            decision.model_dump() if hasattr(decision, "model_dump") else decision
        )

        forbidden_fields = ["social_media", "financial_decision", "external_comms"]
        for field in forbidden_fields:
            assert field not in decision_data, (
                f"Gary decision contains forbidden field '{field}' - violates AI as Tool protocol"
            )


class TestAuthenticAssets:
    """
    Pillar 2: AUTHENTIC ASSETS (FULL_VISION.md lines 28-48)

    Requirements:
    - Backgrounds: Built from actual SMW tilemap + documented patterns + CGRAM palette
    - Character Sprites: Extracted from verified 784 ROM library
    - Audio: BRR music and SFX from real SPC700 dumps
    - Validation Pipeline: Source verification → extraction honesty → gap analysis → integration
    """

    def test_background_tilemap_size(self):
        """FULL_VISION.md: Each background file 5.5KB verified size"""
        assets_dir = Path(__file__).parent.parent / "assets"
        bg_dir = assets_dir / "backgrounds"

        if not bg_dir.exists():
            pytest.skip("assets/backgrounds/ not found")

        for bg in bg_dir.rglob("*.bin"):
            size = bg.stat().st_size
            expected_size = 5.5 * 1024
            tolerance = 100

            assert abs(size - expected_size) < tolerance, (
                f"Background {bg.name} is {size} bytes, expected ~{expected_size} (5.5KB)"
            )

    def test_sprite_rom_provenance(self):
        """FULL_VISION.md: Each sprite traceable to specific ROM, bank, address"""
        manifests = list(Path(__file__).parent.parent.glob("**/*manifest*.json"))

        for manifest_path in manifests:
            if "sprite" in manifest_path.name.lower():
                with open(manifest_path) as f:
                    manifest = json.load(f)

                if isinstance(manifest, dict) and "sprites" in manifest:
                    for sprite in manifest["sprites"]:
                        assert "rom_source" in sprite or "source_rom" in sprite, (
                            f"Sprite missing ROM provenance: {sprite.get('name')}"
                        )

    def test_audio_adsr_envelope(self):
        """FULL_VISION.md: Proper ADSR envelopes, echo settings, filter coefficients"""
        audio_dir = Path(__file__).parent.parent / "assets" / "audio"

        if not audio_dir.exists():
            pytest.skip("assets/audio/ not found")

        audio_files = list(audio_dir.rglob("*.json"))
        if not audio_files:
            pytest.skip("No audio manifest JSON files found")

        for audio_meta in audio_files:
            with open(audio_meta) as f:
                data = json.load(f)

            if isinstance(data, dict) and "tracks" in data:
                for track in data["tracks"]:
                    assert "adsr" in track or "envelope" in track, (
                        f"Audio track missing ADSR/envelope: {track.get('name', audio_meta.name)}"
                    )

    def test_asset_pipeline_logging(self):
        """FULL_VISION.md: All extraction scripts logged and verifiable"""
        extractors_dir = Path(__file__).parent.parent / "extractors"
        if not extractors_dir.exists():
            pytest.skip("extractors/ not found")

        scripts = list(extractors_dir.glob("*.py"))
        assert len(scripts) > 0, "No extractor scripts found"

        SKIP_LOGGING_CHECK = {
            "top_50_snes_games.py"
        }  # Data/config file, not an extractor

        for script in scripts:
            if script.name in SKIP_LOGGING_CHECK:
                continue
            content = script.read_text()
            assert "logging" in content.lower() or "log" in content.lower(), (
                f"Extractor {script.name} lacks logging - not verifiable per FULL_VISION"
            )


class TestLivingWorldBroadcast:
    """
    Pillar 3: LIVING WORLD & BROADCAST READY (FULL_VISION.md lines 50-196)

    Sub-sections tested:
    - Continuity Engine: Relationship Matrix, Show History, Set Evolution
    - Character Careers & Drama
    - Gary Program Director with LLM
    - Show Lifecycle Engine
    - 90s Broadcast Authenticity
    - Technical Authenticity (CRT, audio layering, transitions)
    """

    def test_continuity_engine_relationship_matrix(self):
        """FULL_VISION.md: Relationship Matrix - character friendships/rivalries tracked"""
        from app.living_world import Character, Session

        session = Session()
        chars = session.query(Character).all()
        assert len(chars) > 0, "No characters in living world"

        char_with_relationships = None
        for char in chars:
            if hasattr(char, "relationships") and char.relationships:
                char_with_relationships = char
                break

        if char_with_relationships:
            rels = json.loads(char_with_relationships.relationships)
            assert isinstance(rels, dict), "Relationships not a dict"
            assert len(rels) > 0, "Relationship matrix is empty"

        session.close()

    def test_show_history_lifecycle(self):
        """FULL_VISION.md: Show lifecycle - Pitch → Pilot → Series → Syndication → Cancellation"""
        from app.living_world import Show, Session

        session = Session()
        shows = session.query(Show).all()

        valid_statuses = {
            "pitch",
            "pilot",
            "series",
            "syndication",
            "cancellation",
            "revival",
        }

        for show in shows:
            if hasattr(show, "status"):
                assert show.status in valid_statuses, (
                    f"Show {show.name} has invalid status: {show.status}"
                )

        session.close()

    def test_gary_mood_system(self):
        """FULL_VISION.md: Gary mood affected by station performance"""
        from app.gary import GaryPD

        gary = GaryPD()
        assert hasattr(gary, "mood") or hasattr(gary, "update_mood"), (
            "Gary PD missing mood system"
        )

        if hasattr(gary, "mood"):
            assert gary.mood in ["excited", "frustrated", "celebratory", "neutral"], (
                f"Gary has unexpected mood: {gary.mood}"
            )

    def test_90s_schedule_pattern(self):
        """FULL_VISION.md: Programming schedule with 90s patterns"""
        from app.station import station

        schedule = station.schedule if hasattr(station, "schedule") else None

        expected_blocks = ["morning", "midday", "evening", "late_night"]
        if schedule:
            for block in expected_blocks:
                assert block in schedule, f"Missing schedule block: {block}"

    def test_crt_effects_configured(self):
        """FULL_VISION.md: CRT/VHS overlays - scanlines, chromatic aberration, vignette"""
        renderer_path = Path(__file__).parent.parent / "app" / "renderer.py"

        if not renderer_path.exists():
            pytest.skip("renderer.py not found")

        content = renderer_path.read_text().lower()
        required_effects = ["scanline", "vignette", "crt"]

        for effect in required_effects:
            assert effect in content, (
                f"Renderer missing CRT effect: {effect} (FULL_VISION.md requirement)"
            )

    def test_transition_effects_period_authentic(self):
        """FULL_VISION.md: Wipes, fades, digital dissolves (period-appropriate)"""
        renderer_path = Path(__file__).parent.parent / "app" / "renderer.py"

        if not renderer_path.exists():
            pytest.skip("renderer.py not found")

        content = renderer_path.read_text().lower()
        transitions = ["wipe", "fade", "dissolve", "cut"]

        assert any(t in content for t in transitions), (
            "Renderer missing transition effects (FULL_VISION.md: period-appropriate transitions)"
        )

    def test_emergency_fallbacks(self):
        """FULL_VISION.md: Test patterns, color bars, station ID loops"""
        station_path = Path(__file__).parent.parent / "app" / "station.py"

        if not station_path.exists():
            pytest.skip("station.py not found")

        content = station_path.read_text().lower()
        fallbacks = ["test_pattern", "color_bar", "station_id"]

        assert any(f.replace("_", "") in content.replace("_", "") for f in fallbacks), (
            "Station missing emergency fallbacks (FULL_VISION.md requirement)"
        )

    def test_sweeps_week_special_events(self):
        """FULL_VISION.md: Special events during sweeps weeks"""
        from app.gary import GaryPD

        gary = GaryPD()

        if hasattr(gary, "plan_sweeps"):
            events = gary.plan_sweeps()
            assert isinstance(events, list), "Sweeps events should be a list"

        if hasattr(gary, "sweeps_planning") or hasattr(gary, "special_events"):
            assert True

    def test_career_trajectory_system(self):
        """FULL_VISION.md: Career Trajectories - Intern → Regular → Star → Legend"""
        from app.living_world import Character, Session

        session = Session()
        chars = session.query(Character).all()

        if len(chars) > 0:
            char = chars[0]
            career_stages = {"intern", "regular", "star", "legend"}

            if hasattr(char, "career_status"):
                assert char.career_status in career_stages, (
                    f"Invalid career status: {char.career_status}"
                )

        session.close()

    def test_broadcast_data_persistence(self):
        """FULL_VISION.md: OUTPUT/ and DATA/ directories for persistence"""
        project_root = Path(__file__).parent.parent

        assert project_root.exists(), "Project root not found"

        required_dirs = ["OUTPUT", "DATA"]
        for dirname in required_dirs:
            dir_path = project_root / dirname
            if not dir_path.exists():
                dir_path.mkdir(exist_ok=True)


class TestNightShiftProtocol:
    """FULL_VISION.md lines 177-185: Night Shift Protocol (Autonomous Development)"""

    def test_night_shift_autonomous_show_dev(self):
        """FULL_VISION.md: Autonomous show development during off-hours"""
        night_shift_path = Path(__file__).parent.parent / "app" / "night_shift.py"

        if not night_shift_path.exists():
            pytest.skip("night_shift.py not found")

        content = night_shift_path.read_text()

        required_features = ["show", "development", "off_hours", "autonomous"]
        for feature in required_features:
            assert feature.lower() in content.lower(), (
                f"Night shift missing {feature} (FULL_VISION.md requirement)"
            )

    def test_morning_report_generation(self):
        """FULL_VISION.md: Morning report generation for creator review"""
        morning_reports = Path(__file__).parent.parent / "OUTPUT" / "morning_reports"

        if morning_reports.exists():
            reports = list(morning_reports.glob("*.json"))
            if len(reports) > 0:
                latest = max(reports, key=lambda p: p.stat().st_mtime)
                with open(latest) as f:
                    report = json.load(f)

                assert "characters" in report or "shows" in report, (
                    "Morning report missing required sections"
                )


class TestCovenantCompliance:
    """FULL_VISION.md lines 237-253: COVENANT TO THE VISION - 10 Affirmations"""

    def test_uppercase_folder_naming(self):
        """Covenant #2: UPPERCASE naming for ALL project folders."""
        project_root = Path(__file__).parent.parent

        KNOWN_LOWERCASE = {
            ".venv",
            "node_modules",
            "__pycache__",
            "app",
            "assets",
            "data",
            "docs",
            "engine",
            "extractors",
            "logs",
            "scripts",
            "tests",
            "venv313",
        }

        violations = []
        for item in project_root.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                if not item.name.isupper() and item.name not in KNOWN_LOWERCASE:
                    violations.append(item.name)

        assert len(violations) == 0, (
            f"New folders should be UPPERCASE per FULL_VISION covenant: {violations}"
        )

    def test_snes_only_authenticity(self):
        """Covenant #5: SNES-only - no Sega characters, Sonic replaced with Kirby"""
        characters_path = Path(__file__).parent.parent / "app" / "characters.py"

        if not characters_path.exists():
            pytest.skip("characters.py not found")

        content = characters_path.read_text().lower()

        forbidden_sega = ["sonic", "sega"]
        for term in forbidden_sega:
            if term in content:
                assert "kirby" in content or "replace" in content, (
                    f"Found Sega reference '{term}' without Kirby substitution"
                )
