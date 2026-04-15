"""
SNES Scene Engine - Gary's Interface to Authentic SNES Game Logic

This module provides Gary with programmatic access to SNES ROM assets,
enabling accurate scene creation that feels authentically SNES.

Usage by Gary:
    from app.snes_scene_engine import SNESSceneEngine, SceneDirector

    # Initialize engine with ROM library
    engine = SNESSceneEngine()

    # Create a scene from a game
    scene = SceneDirector.create_scene(
        game="SUPER MARIOWORLD",
        scene_type="castle_confrontation",
        elements=["bowser", "peach", "castle_bg", "smw_battle_music"]
    )

    # Add specific sprite at position
    scene.add_character("mario", pose="jump", position=(100, 200))

    # Trigger audio
    scene.play_music("smw_bowser")
    scene.play_sfx("smw_powerup")
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from extractors.world_asset_extractor import (
    WorldAssetExtractor,
    CHARACTER_SPRITES,
    AUDIO_TRACKS,
    GENRE_BACKGROUNDS,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SpriteReference:
    """Reference to a sprite from a specific game."""

    character: str
    game: str
    rom_hash: str
    rom_path: str
    bank: int
    offset: int
    frames: int
    poses: dict[str, int] = field(default_factory=dict)

    def to_gary_command(self) -> str:
        """Generate Gary command for this sprite."""
        return f"SPRITE:{self.character}@{self.game}:bank={hex(self.bank)},offset={hex(self.offset)}"


@dataclass
class AudioReference:
    """Reference to audio from a specific game."""

    track_name: str
    game: str
    addr: int
    audio_type: str
    rom_hash: str

    def to_gary_command(self) -> str:
        return f"AUDIO:{self.track_name}@{self.game}:addr={hex(self.addr)},type={self.audio_type}"


@dataclass
class BackgroundReference:
    """Reference to background from a specific game."""

    genre: str
    game: str
    addr: int
    size: tuple[int, int]
    rom_hash: str

    def to_gary_command(self) -> str:
        return f"BG:{self.genre}@{self.game}:addr={hex(self.addr)},size={self.size}"


@dataclass
class SceneElement:
    """A single element in a scene."""

    element_type: Literal[
        "character", "background", "audio", "sfx", "tilemap", "palette"
    ]
    name: str
    game: str
    reference: SpriteReference | AudioReference | BackgroundReference
    position: tuple[int, int] | None = None
    layer: int = 0
    animation: str | None = None
    trigger_time: float | None = None


@dataclass
class SNESScene:
    """
    A complete SNES-style scene ready for Gary to direct.

    Gary can modify this scene programmatically before rendering.
    """

    scene_id: str
    scene_type: str
    game: str
    elements: list[SceneElement] = field(default_factory=list)
    music: AudioReference | None = None
    palette: list[bytes] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def add_character(
        self,
        character: str,
        pose: str = "idle",
        position: tuple[int, int] = (128, 200),
        layer: int = 1,
    ) -> SceneElement:
        """Add a character to the scene."""
        engine = SNESSceneEngine.get_instance()
        ref = engine.get_sprite_reference(character)

        element = SceneElement(
            element_type="character",
            name=character,
            game=ref.game,
            reference=ref,
            position=position,
            layer=layer,
            animation=pose,
        )
        self.elements.append(element)
        return element

    def set_background(self, genre: str, game: str | None = None) -> SceneElement:
        """Set the background for the scene."""
        engine = SNESSceneEngine.get_instance()
        ref = engine.get_background_reference(genre, game)

        element = SceneElement(
            element_type="background", name=genre, game=ref.game, reference=ref, layer=0
        )
        self.elements.insert(0, element)
        return element

    def play_music(self, track: str) -> None:
        """Set the background music for the scene."""
        engine = SNESSceneEngine.get_instance()
        self.music = engine.get_audio_reference(track)

    def add_sfx(self, sfx: str, time: float = 0) -> SceneElement:
        """Add a sound effect to the scene."""
        engine = SNESSceneEngine.get_instance()
        ref = engine.get_audio_reference(sfx)

        element = SceneElement(
            element_type="sfx",
            name=sfx,
            game=ref.game,
            reference=ref,
            trigger_time=time,
        )
        self.elements.append(element)
        return element

    def to_gary_script(self) -> str:
        """Generate a Gary-readable script for this scene."""
        lines = [
            f"# SCENE: {self.scene_id}",
            f"# TYPE: {self.scene_type}",
            f"# GAME: {self.game}",
            "",
        ]

        for el in self.elements:
            if el.element_type == "background":
                lines.append(f"SET_BG({el.name}, layer={el.layer})")
            elif el.element_type == "character":
                pos = el.position or (0, 0)
                lines.append(
                    f"CHARACTER({el.name}, pose={el.animation}, pos=({pos[0]},{pos[1]}), layer={el.layer})"
                )
            elif el.element_type == "sfx":
                time = el.trigger_time or 0
                lines.append(f"SFX({el.name}, time={time})")

        if self.music:
            lines.append(f"MUSIC({self.music.track_name})")

        lines.append("")
        lines.append("# END_SCENE")
        return "\n".join(lines)

    def to_api_call(self) -> dict:
        """Generate API call parameters for the renderer."""
        return {
            "scene_id": self.scene_id,
            "scene_type": self.scene_type,
            "game": self.game,
            "backgrounds": [
                {
                    "name": el.name,
                    "game": el.game,
                    "ref": el.reference.to_gary_command(),
                    "layer": el.layer,
                }
                for el in self.elements
                if el.element_type == "background"
            ],
            "characters": [
                {
                    "name": el.name,
                    "game": el.game,
                    "ref": el.reference.to_gary_command(),
                    "pose": el.animation,
                    "position": el.position,
                    "layer": el.layer,
                }
                for el in self.elements
                if el.element_type == "character"
            ],
            "sfx": [
                {
                    "name": el.name,
                    "ref": el.reference.to_gary_command(),
                    "trigger_time": el.trigger_time,
                }
                for el in self.elements
                if el.element_type == "sfx"
            ],
            "music": self.music.to_gary_command() if self.music else None,
        }


class GameSceneLibrary:
    """
    Pre-built scene templates for each game.
    Gary can use these as foundations or reference them for authentic staging.
    """

    SCENE_TEMPLATES = {
        "SUPER MARIOWORLD": {
            "castle_confrontation": {
                "elements": ["bowser_idle", "peach_idle", "castle_bg"],
                "music": "smw_bowser",
                "sfx": ["smw_jump", "smw_powerup"],
                "typical_duration": 30.0,
                "camera_notes": "Wide shot, castle interior, Bowser center-left, Peach right, Mario far right",
            },
            "overworld_meadow": {
                "elements": ["mario_idle", "yoshi_idle", "forest_bg"],
                "music": "smw_grass",
                "sfx": ["smw_jump"],
                "typical_duration": 15.0,
                "camera_notes": "Medium shot, outdoor grass level, bright palette",
            },
            "underground_treasure": {
                "elements": ["mario_idle", "underground_bg"],
                "music": "smw_underground",
                "typical_duration": 20.0,
                "camera_notes": "Close-up, underground cave, darker palette",
            },
            "airship_assault": {
                "elements": ["mario_idle", "bowser_idle", "airship_bg"],
                "music": "smw_airship",
                "sfx": ["smw_coin", "smw_powerup"],
                "typical_duration": 25.0,
                "camera_notes": "Action shot, airship deck, dramatic angles",
            },
        },
        "THE LEGEND OF ZELDA": {
            "triforce_revelation": {
                "elements": ["link_idle", "zelda_idle", "ganon_idle", "mystical_bg"],
                "music": "zelda_boss",
                "typical_duration": 45.0,
                "camera_notes": "Wide cinematic, Light World temple, triangle formation",
            },
            "hyrule_overworld": {
                "elements": ["link_idle", "forest_bg"],
                "music": "zelda_overworld",
                "typical_duration": 20.0,
                "camera_notes": "Medium shot, top-down perspective, green palette dominant",
            },
            "dungeon_exploration": {
                "elements": ["link_idle", "castle_bg"],
                "music": "zelda_dungeon",
                "typical_duration": 30.0,
                "camera_notes": "Over-shoulder, dungeon room, torch-lit atmosphere",
            },
        },
        "EarthBound": {
            "boss_encounter": {
                "elements": [
                    "ness_idle",
                    "paula_idle",
                    "jeff_idle",
                    "poo_idle",
                    "battle_bg",
                ],
                "music": "eb_fateful",
                "typical_duration": 60.0,
                "camera_notes": "Turn-based battle UI, PSI menu visible, enemy center",
            },
            "peaceful_twoson": {
                "elements": ["ness_idle", "city_bg"],
                "music": "eb_katy",
                "typical_duration": 15.0,
                "camera_notes": "Overhead town view, bright colors, NPC crowds",
            },
        },
        "CHRONO TRIGGER": {
            "final_battle": {
                "elements": [
                    "crono_idle",
                    "marle_idle",
                    "lucca_idle",
                    "frog_idle",
                    "magus_idle",
                    "battle_bg",
                ],
                "music": "ct_battle",
                "typical_duration": 90.0,
                "camera_notes": "7-character lineup, spell effects layer, dramatic lighting",
            },
            "ocean_palace": {
                "elements": ["crono_idle", "mystical_bg"],
                "music": "ct_main",
                "typical_duration": 25.0,
                "camera_notes": "Underwater palace, blue-green palette, parallax scrolling",
            },
        },
        "DONKEY KONG COUNTRY": {
            "forest_bridge": {
                "elements": ["dk_idle", "diddy_idle", "forest_bg"],
                "music": "dk_terrain",
                "typical_duration": 20.0,
                "camera_notes": "Side-scrolling platforming, pre-rendered 3D backgrounds",
            },
            "waterfall_escape": {
                "elements": ["dk_idle", "diddy_idle", "forest_bg"],
                "music": "dk_waterfall",
                "typical_duration": 30.0,
                "camera_notes": "Barrel-cannon sequence, rushing water effects",
            },
        },
        "STAR FOX": {
            "corneria_intro": {
                "elements": ["fox_idle", "falco_idle", "space_bg"],
                "music": "starfox_main",
                "typical_duration": 20.0,
                "camera_notes": "3D polygon corridor, ship flythrough",
            },
            "area_6_assault": {
                "elements": ["fox_idle", "wolf_idle", "space_bg"],
                "music": "starfox_area_6",
                "typical_duration": 35.0,
                "camera_notes": "Dogfight sequence, laser trails, explosion layers",
            },
        },
        "KIRBY SUPER DELUXE": {
            "green_greens": {
                "elements": ["kirby_idle", "metaknight_idle", "forest_bg"],
                "music": "kirby_green",
                "typical_duration": 15.0,
                "camera_notes": "Bright pastel palette, bouncy platforming",
            },
            "checkerboard_challenge": {
                "elements": ["kirby_idle", "kingdedede_idle", "battle_bg"],
                "music": "kirby_checker",
                "typical_duration": 25.0,
                "camera_notes": "Boss arena, checkerboard floor pattern",
            },
        },
        "MORTAL KOMBAT": {
            "fatality_finish": {
                "elements": ["liu_kang_idle", "scorpion_idle", "battle_bg"],
                "music": "mk_fatality",
                "sfx": [],
                "typical_duration": 15.0,
                "camera_notes": "Close-up fatality hit, red flash, brutal impact",
            },
            "versus_screen": {
                "elements": ["subzero_idle", "scorpion_idle", "battle_bg"],
                "music": "mk_round",
                "typical_duration": 5.0,
                "camera_notes": "Split screen character select, vs text animation",
            },
        },
        "STREET FIGHTER 2": {
            "hadouken_clash": {
                "elements": ["ryu_idle", "ken_idle", "city_bg"],
                "music": "sf2_vs",
                "typical_duration": 30.0,
                "camera_notes": "Fight sequence, special move exchanges",
            },
            "character_select": {
                "elements": ["ryu_idle", "chunli_idle", "sf2_char_select"],
                "music": "sf2_char_select",
                "typical_duration": 10.0,
                "camera_notes": "Character select grid, portrait showcases",
            },
        },
        "CONTRA3 THE ALIEN WAR": {
            "alien_invasion": {
                "elements": ["battle_bg"],
                "music": "contra_rumble",
                "typical_duration": 25.0,
                "camera_notes": "Run-and-gun action, alien horde, side-scrolling",
            }
        },
        "FINAL FIGHT": {
            "street_brawl": {
                "elements": ["guy", "cody", "maki", "city_bg"],
                "music": "ff_street",
                "typical_duration": 30.0,
                "camera_notes": "Side-scrolling beat-em-up, urban city backdrop",
            },
            "boss_fight": {
                "elements": ["guy", "cody", "battle_bg"],
                "music": "ff_fight",
                "typical_duration": 20.0,
                "camera_notes": "Close combat, impact effects, combo sequences",
            },
        },
        "SUPER MARIO KART": {
            "rainbow_road": {
                "elements": [
                    "mario_kart",
                    "luigi_kart",
                    "yoshi_kart",
                    "bowser_kart",
                    "sky_bg",
                ],
                "music": "smk_mario",
                "typical_duration": 60.0,
                "camera_notes": "Racing mode, kart sprites, parallax track scrolling",
            },
            "battle_mode": {
                "elements": ["mario_kart", "koopa_kart", "battle_bg"],
                "music": "smk_battle",
                "typical_duration": 45.0,
                "camera_notes": "Balloon battle, arena backdrop",
            },
        },
        "SUPER STAR WARS": {
            "cantina_scene": {
                "elements": ["luke", "han", "chewie", "city_bg"],
                "music": "ssw_cantina",
                "typical_duration": 30.0,
                "camera_notes": "Alien crowd, Mos Eisley ambiance, exotic patrons",
            },
            "saber_duel": {
                "elements": ["luke", "luke_saber", "battle_bg"],
                "music": "ssw_battle",
                "typical_duration": 45.0,
                "camera_notes": "Lightsaber clash, Force effects, dramatic lighting",
            },
        },
        "EARTHWORM JIM": {
            "cowtilion": {
                "elements": ["earthworm_jim_idle", "earthworm_jim_gun", "space_bg"],
                "music": "ewj_action",
                "typical_duration": 25.0,
                "camera_notes": "Wacky space action, bouncy physics, cow in helmet",
            },
            "hero_mode": {
                "elements": ["earthworm_jim_run", "earthworm_jim_gun", "battle_bg"],
                "music": "ewj_boss",
                "typical_duration": 30.0,
                "camera_notes": "Fast-paced platforming, weapon upgrades visible",
            },
        },
        "BATTLETOADS IN BATTLEMANIACS": {
            "rat_race": {
                "elements": ["rash_idle", "zitz_idle", "pimple_idle", "battle_bg"],
                "music": "bt_level",
                "typical_duration": 35.0,
                "camera_notes": "Speedy combat, tongue attacks, cartoon violence",
            },
            "bike_boss": {
                "elements": ["rash_bike", "rash_tongue", "battle_bg"],
                "music": "bt_boss",
                "typical_duration": 40.0,
                "camera_notes": "Motorcycle sequence, wall riding, boss patterns",
            },
        },
        "CLAY FIGHTER": {
            "clay_cage_match": {
                "elements": ["clayf_idle", "badMrFrosty_idle", "battle_bg"],
                "music": "cf_fight",
                "typical_duration": 45.0,
                "camera_notes": "Claymation style, exaggerated hits, slime effects",
            },
            "tornado_clash": {
                "elements": ["clayf_slam", "tNtu_idle", "battle_bg"],
                "music": "cf_win",
                "typical_duration": 30.0,
                "camera_notes": "Special moves, tornado effects, victory poses",
            },
        },
        "ART OF FIGHTING": {
            "dojo_training": {
                "elements": ["ryuuzaru_idle", "wongee_idle", "dojo_bg"],
                "music": "aof_theme",
                "typical_duration": 20.0,
                "camera_notes": "Training mode, martial arts demonstrations",
            },
            "tournament_fight": {
                "elements": ["ryuuzaru_fire", "wongee_shot", "battle_bg"],
                "music": "aof_fight",
                "typical_duration": 45.0,
                "camera_notes": "Street fighting, special move effects, dramatic cuts",
            },
        },
        "ACTRaiser": {
            "divine_intervention": {
                "elements": ["god_idle", "god_miracle", "mystical_bg"],
                "music": "act_title",
                "typical_duration": 35.0,
                "camera_notes": "God's perspective, world building, miracles",
            },
            "demon_battle": {
                "elements": ["god_miracle", "battle_bg"],
                "music": "act_battle",
                "typical_duration": 50.0,
                "camera_notes": "Divine combat, lightning effects, angelic choir",
            },
        },
        "LEGEND OF THE MYSTICAL NINJA": {
            "ninja_training": {
                "elements": ["geebeetle_idle", "yuki_idle", "forest_bg"],
                "music": "lmn_title",
                "typical_duration": 20.0,
                "camera_notes": "Ninja antics, colorful visuals, playful action",
            },
            "boss_battle": {
                "elements": ["geebeetle_shot", "yuki_snow", "battle_bg"],
                "music": "lmn_boss",
                "typical_duration": 35.0,
                "camera_notes": "Magic effects, snow attacks, boss patterns",
            },
        },
        # TV Show Scene Templates
        "THE SIMPSONS": {
            "couch_gag": {
                "elements": [
                    "bart_idle",
                    "homer_idle",
                    "marge_idle",
                    "lisa_idle",
                    "maggie_idle",
                    "cartoon_house",
                ],
                "music": "simpsons_theme",
                "typical_duration": 15.0,
                "camera_notes": "Family on couch, laugh track, classic sitcom feel",
            },
            "elementary_school": {
                "elements": ["bart_idle", "bart_nelson", "school"],
                "music": "simpsons_school",
                "typical_duration": 20.0,
                "camera_notes": "Classroom chaos, chalkboard gag potential",
            },
            "duff_garden": {
                "elements": ["homer_idle", "duff_garden_bg"],
                "music": "simpsons_bar",
                "typical_duration": 25.0,
                "camera_notes": "Bar setting, beer goggles effect, Moe's Tavern vibe",
            },
            "nuclear_plant": {
                "elements": ["homer_idle", "power_plant"],
                "music": "simpsons_plant",
                "typical_duration": 30.0,
                "camera_notes": "Nuclear plant control room, safety violations",
            },
            "krusty_show": {
                "elements": ["krusty_idle", "studio_bg"],
                "music": "simpsons_krusty",
                "typical_duration": 45.0,
                "camera_notes": "TV studio, live broadcast feel, cartoon crowd",
            },
        },
        "BEAVIS AND BUTT-HEAD": {
            "taco_world": {
                "elements": ["beavis_idle", "butthead_idle", "town_bg"],
                "music": "beavis_theme",
                "typical_duration": 20.0,
                "camera_notes": "Teenage hangout, fast food aesthetic, couch commentary",
            },
            "butt-head_commentary": {
                "elements": ["beavis_butch", "butthead_laughing", "couch_bg"],
                "music": "beavis_couch",
                "typical_duration": 15.0,
                "camera_notes": "Couch commentary, MTV-style presentation, teen humor",
            },
        },
        "REN AND STIMPY": {
            "stimpy_saloon": {
                "elements": ["ren_idle", "stimpy_idle", "saloon_bg"],
                "music": "ren_stimpy_theme",
                "typical_duration": 20.0,
                "camera_notes": "Wild west saloon, gross-out humor, 90s cartoon aesthetic",
            },
            "space_madness": {
                "elements": ["ren_angry", "stimpy_happy", "space_bg"],
                "music": "ren_stimpy_space",
                "typical_duration": 25.0,
                "camera_notes": "Space adventure, gross鼻涕 effects, cartoon violence",
            },
        },
        "ANIMANIACS": {
            "water_tower": {
                "elements": ["yakko_idle", "wakko_idle", "dot_idle", "cartoon_house"],
                "music": "animaniacs_theme",
                "typical_duration": 15.0,
                "camera_notes": "Warner siblings, slapstick comedy, musical numbers",
            },
            "slapstick_studio": {
                "elements": ["yakko_dance", "dot_cutey", "studio_bg"],
                "music": "animaniacs_show",
                "typical_duration": 20.0,
                "camera_notes": "Variety show format, cartoon characters breaking fourth wall",
            },
        },
        "THE FLINTSTONES": {
            "bedrock_living": {
                "elements": [
                    "fred_idle",
                    "wilma_idle",
                    "pebbles_idle",
                    "bamm_bamm_idle",
                    "cartoon_house",
                ],
                "music": "flintstones_theme",
                "typical_duration": 20.0,
                "camera_notes": "Prehistoric sitcom, stone-age tech, family comedy",
            },
            "bowling_league": {
                "elements": ["fred_wwf", "barney_idle", "bowling_alley_bg"],
                "music": "flintstones_bowling",
                "typical_duration": 25.0,
                "camera_notes": "Dino bowling, slapstick sports, Hanna-Barbera style",
            },
        },
        "THE JETSONS": {
            "orbit_cinema": {
                "elements": [
                    "george_idle",
                    "jane_idle",
                    "judy_idle",
                    "elroy_idle",
                    "space_station",
                ],
                "music": "jetsons_theme",
                "typical_duration": 20.0,
                "camera_notes": "Futuristic sitcom, flying cars, space-age gadgets",
            },
            "cosmic_business": {
                "elements": ["george_idle", "business_office"],
                "music": "jetsons_office",
                "typical_duration": 25.0,
                "camera_notes": "Space office, robot assistants, corporate comedy",
            },
        },
        # Game Show Scene Templates
        "WHEEL OF FORTUNE": {
            "main_game": {
                "elements": ["wheel_host_idle", "wheel_spin", "game_show"],
                "music": "wheel_theme",
                "typical_duration": 45.0,
                "camera_notes": "Puzzle board, spinning wheel, contestant positions",
            },
            "bonus_round": {
                "elements": ["wheel_winner", "bonus_round_bg"],
                "music": "wheel_bonus",
                "typical_duration": 30.0,
                "camera_notes": "Big money round, dramatic tension, Vanna energy",
            },
        },
        "JEOPARDY": {
            "main_game": {
                "elements": ["alex_trebek_idle", "alex_answer", "jeopardy_board"],
                "music": "jeopardy_theme",
                "typical_duration": 60.0,
                "camera_notes": "Answer and question format, podium positions, scoreboard",
            },
            "final_jeopardy": {
                "elements": ["alex_trebek_idle", "jeopardy_daily_double", "final_bg"],
                "music": "jeopardy_final",
                "typical_duration": 15.0,
                "camera_notes": "Wagering drama, category reveal, tension music",
            },
        },
        "FAMILY FEUD": {
            "fast_money": {
                "elements": [
                    "familyfeud_host_idle",
                    "familyfeud_buzzer",
                    "familyfeud_x",
                ],
                "music": "familyfeud_theme",
                "typical_duration": 30.0,
                "camera_notes": "Survey says..., face-offs, blue X marks, strike sounds",
            },
        },
        # Superhero/Movie Scene Templates
        "BATMAN FOREVER": {
            "gotham_streets": {
                "elements": [
                    "batman_idle",
                    "batman_cape",
                    "batman_punch",
                    "action_set",
                ],
                "music": "batman_theme",
                "typical_duration": 30.0,
                "camera_notes": "Dark city vibes, neon signs, bat-signal in sky",
            },
            "riddler_riddle": {
                "elements": ["batman_idle", "riddler_idle", "museum"],
                "music": "batman_riddler",
                "typical_duration": 25.0,
                "camera_notes": "Puzzle solving, riddles, campy villain energy",
            },
        },
        "SPIDER-MAN": {
            "web_swinging": {
                "elements": ["spiderman_idle", "spiderman_swing", "tower"],
                "music": "spiderman_theme",
                "typical_duration": 35.0,
                "camera_notes": "NYC skyline, web-slinging action, hero landing poses",
            },
            "venom_clash": {
                "elements": ["spiderman_punch", "venom_idle", "action_set"],
                "music": "spiderman_venom",
                "typical_duration": 40.0,
                "camera_notes": "Dark symbiote vibes, urban destruction, mirror match",
            },
        },
        "MIGHTY MORPHIN POWER RANGERS": {
            "morphing_time": {
                "elements": [
                    "redranger_idle",
                    "blueranger_idle",
                    "yelloweranger_idle",
                    "action_set",
                ],
                "music": "powerrangers_theme",
                "typical_duration": 30.0,
                "camera_notes": "Power Rangers morph, color-coded heroes, teen angst",
            },
            "megazord_finale": {
                "elements": [
                    "redranger_power",
                    "zordon_idle",
                    "alpha5_idle",
                    "battle_bg",
                ],
                "music": "powerrangers_megazord",
                "typical_duration": 45.0,
                "camera_notes": "Giant robot combine, final boss energy, save the day",
            },
        },
        # Sports Broadcast Scene Templates
        "NBA JAM": {
            "slam_contest": {
                "elements": [
                    "nbajam_player1",
                    "nbajam_dunk",
                    "nbajam_on_fire",
                    "sports_arena",
                ],
                "music": "nbajam_theme",
                "typical_duration": 30.0,
                "camera_notes": "On fire mode, crazy dunks, arcade sports energy",
            },
            "two_on_two": {
                "elements": [
                    "nbajam_player1",
                    "nbajam_player2",
                    "nbajam_dunk",
                    "sports_arena",
                ],
                "music": "nbajam_game",
                "typical_duration": 25.0,
                "camera_notes": "Fast-paced basketball, screen shake, crowd cheering",
            },
        },
        # Looney Tunes Scene Templates
        "LOONEY TUNES": {
            "acme_chaos": {
                "elements": ["bugs_idle", "bugs_carrot", "bugs_punch", "desert_bg"],
                "music": "looney_theme",
                "typical_duration": 20.0,
                "camera_notes": "Cartoon violence, anvils falling, ACME products",
            },
            "duck_duel": {
                "elements": ["daffy_idle", "daffy_duel", "studio_bg"],
                "music": "looney_duck",
                "typical_duration": 15.0,
                "camera_notes": "Daffy's drama, theatrical flair, slapstick comedy",
            },
        },
        # Arcade Scene Templates
        "PAC-MAN 2": {
            "ghost_chase": {
                "elements": [
                    "pacman_idle",
                    "pacman_eat",
                    "ghost_idle",
                    "ghost_vulnerable",
                    "arcade_cabinet",
                ],
                "music": "pacman_theme",
                "typical_duration": 25.0,
                "camera_notes": "Classic arcade maze, power pellets, ghost scared mode",
            },
        },
    }

    @classmethod
    def get_template(cls, game: str, scene_type: str) -> dict | None:
        """Get a pre-built scene template."""
        return cls.SCENE_TEMPLATES.get(game, {}).get(scene_type)

    @classmethod
    def list_scenes_for_game(cls, game: str) -> list[str]:
        """List all available scene types for a game."""
        return list(cls.SCENE_TEMPLATES.get(game, {}).keys())

    @classmethod
    def list_all_games(cls) -> list[str]:
        """List all games with scene templates."""
        return list(cls.SCENE_TEMPLATES.keys())


class SceneDirector:
    """
    Gary's primary interface for directing scenes.

    This class provides high-level scene creation methods
    that combine ROM asset references with authentic game logic.
    """

    def __init__(self, engine: "SNESSceneEngine | None" = None):
        self.engine = engine or SNESSceneEngine.get_instance()
        self.scene_templates = GameSceneLibrary()

    def create_scene(
        self, game: str, scene_type: str, customizations: dict | None = None
    ) -> SNESScene:
        """
        Create a scene from a template with optional customizations.

        Args:
            game: The source game (e.g., "SUPER MARIOWORLD")
            scene_type: The scene template (e.g., "castle_confrontation")
            customizations: Optional overrides for elements, positions, etc.

        Returns:
            SNESScene ready for Gary to modify or render
        """
        template = self.scene_templates.get_template(game, scene_type)
        if not template:
            raise ValueError(
                f"No template for {game}/{scene_type}. Available: {self.scene_templates.list_scenes_for_game(game)}"
            )

        scene_id = f"{game}_{scene_type}_{len(self.engine.created_scenes)}"
        scene = SNESScene(
            scene_id=scene_id,
            scene_type=scene_type,
            game=game,
            metadata={
                "typical_duration": template.get("typical_duration", 30.0),
                "camera_notes": template.get("camera_notes", ""),
            },
        )

        if customizations:
            elements_to_add = customizations.get(
                "elements", template.get("elements", [])
            )
        else:
            elements_to_add = template.get("elements", [])

        for i, element_name in enumerate(elements_to_add):
            if element_name in ["mario", "luigi", "yoshi", "bowser", "peach", "toad"]:
                scene.add_character(element_name, position=(100 + i * 80, 200))
            elif element_name in ["link", "zelda", "ganon", "impa", "sahasrahla"]:
                scene.add_character(element_name, position=(100 + i * 80, 200))
            elif element_name in ["ness", "paula", "jeff", "poo", "walrus", "teddy"]:
                scene.add_character(element_name, position=(100 + i * 60, 200))
            elif element_name in ["fox", "falco", "wolf", "pigma"]:
                scene.add_character(element_name, position=(100 + i * 80, 200))
            elif element_name in ["dk", "diddy", "dixie", "cranky", "funky", "candy"]:
                scene.add_character(element_name, position=(100 + i * 80, 200))
            elif element_name in [
                "crono",
                "marle",
                "lucca",
                "frog",
                "magus",
                "ayla",
                "rob",
            ]:
                scene.add_character(element_name, position=(100 + i * 60, 200))
            elif element_name in [
                "ryu",
                "ken",
                "chunli",
                "guile",
                "zangief",
                "dhalsim",
                "sagat",
            ]:
                scene.add_character(element_name, position=(100 + i * 80, 200))
            elif element_name in ["kirby", "metaknight", "kingdedede"]:
                scene.add_character(element_name, position=(100 + i * 80, 200))
            elif element_name in ["megaman", "zero"]:
                scene.add_character(element_name, position=(100 + i * 80, 200))
            elif element_name in [
                "liu_kang",
                "scorpion",
                "subzero",
                "raiden",
                "sonya",
                "jax",
                "kano",
            ]:
                scene.add_character(element_name, position=(100 + i * 80, 200))
            elif element_name in ["guy", "cody", "maki"]:
                scene.add_character(element_name, position=(100 + i * 80, 200))
            elif element_name in ["rash", "zitz", "pimple"]:
                scene.add_character(element_name, position=(100 + i * 80, 200))
            elif element_name in ["luke", "leia", "han", "chewie", "lando"]:
                scene.add_character(element_name, position=(100 + i * 80, 200))
            elif element_name in [
                "earthworm_jim_idle",
                "earthworm_jim_run",
                "earthworm_jim_gun",
                "psycrow",
            ]:
                scene.add_character(element_name, position=(100 + i * 80, 200))
            elif element_name in ["clayf_idle", "badMrFrosty_idle", "tNtu_idle"]:
                scene.add_character(element_name, position=(100 + i * 80, 200))
            elif element_name in ["ryuuzaru_idle", "wongee_idle"]:
                scene.add_character(element_name, position=(100 + i * 80, 200))
            elif element_name in ["god_idle", "god_miracle"]:
                scene.add_character(element_name, position=(100 + i * 80, 200))
            elif element_name in ["geebeetle_idle", "yuki_idle"]:
                scene.add_character(element_name, position=(100 + i * 80, 200))
            elif element_name in ["leo", "raph", "don", "mike"]:
                scene.add_character(element_name, position=(100 + i * 60, 200))
            elif "_kart" in element_name:
                scene.add_character(element_name, position=(100 + i * 80, 200))
            elif (
                "_idle" in element_name
                or "_walk" in element_name
                or "_run" in element_name
            ):
                scene.add_character(element_name, position=(100 + i * 80, 200))
            elif (
                "_shoot" in element_name
                or "_slash" in element_name
                or "_shot" in element_name
            ):
                scene.add_character(element_name, position=(100 + i * 80, 200))
            elif "_bg" in element_name:
                genre = element_name.replace("_bg", "")
                scene.set_background(genre)
            elif "battle_bg" in element_name:
                scene.set_background("battle")
            elif "city_bg" in element_name:
                scene.set_background("city")
            elif "mystical_bg" in element_name:
                scene.set_background("mystical")
            elif "space_bg" in element_name:
                scene.set_background("space")
            elif "forest_bg" in element_name:
                scene.set_background("forest")
            elif "castle_bg" in element_name:
                scene.set_background("castle")
            elif "underground_bg" in element_name:
                scene.set_background("underwater")
            elif "airship_bg" in element_name:
                scene.set_background("battle")

        if "music" in template:
            scene.play_music(template["music"])

        if "sfx" in template:
            for i, sfx in enumerate(template["sfx"]):
                scene.add_sfx(sfx, time=i * 0.5)

        self.engine.created_scenes.append(scene)
        logger.info(f"Created scene: {scene_id}")
        return scene

    def create_custom_scene(
        self,
        game: str,
        characters: list[str] | None = None,
        background: str | None = None,
        music: str | None = None,
        sfx: list[str] | None = None,
        scene_id: str | None = None,
    ) -> SNESScene:
        """Create a completely custom scene from components."""
        scene_id = scene_id or f"custom_{game}_{len(self.engine.created_scenes)}"

        scene = SNESScene(scene_id=scene_id, scene_type="custom", game=game)

        if background:
            scene.set_background(background, game)

        if characters:
            for i, char in enumerate(characters):
                scene.add_character(char, position=(100 + i * 80, 200))

        if music:
            scene.play_music(music)

        if sfx:
            for i, sfx_name in enumerate(sfx):
                scene.add_sfx(sfx_name, time=i * 0.5)

        self.engine.created_scenes.append(scene)
        return scene

    def describe_scene_for_gary(self, scene: SNESScene) -> str:
        """Generate a natural language description of a scene for Gary."""
        chars = [e.name for e in scene.elements if e.element_type == "character"]
        bg = next(
            (e.name for e in scene.elements if e.element_type == "background"), None
        )
        music = scene.music.track_name if scene.music else None

        desc = f"Scene '{scene.scene_id}' from {scene.game}:\n"
        if bg:
            desc += f"  Background: {bg}\n"
        if chars:
            desc += f"  Characters: {', '.join(chars)}\n"
        if music:
            desc += f"  Music: {music}\n"
        if scene.metadata.get("camera_notes"):
            desc += f"  Camera: {scene.metadata['camera_notes']}\n"

        return desc


class SNESSceneEngine:
    """
    The core engine for SNES scene creation.

    This singleton provides Gary with access to:
    - ROM asset references
    - Scene creation and management
    - Authenticated game logic
    """

    _instance = None

    def __init__(self, manifest_path: str = "ROM_SOURCE/roms_manifest.json"):
        self.manifest_path = Path(manifest_path)
        self.asset_extractor = WorldAssetExtractor(self.manifest_path, Path("ASSETS"))
        self.scenes: list[SNESScene] = []
        self.created_scenes: list[SNESScene] = []
        self.director = SceneDirector(self)
        self._sprite_cache: dict[str, SpriteReference] = {}
        self._audio_cache: dict[str, AudioReference] = {}
        self._bg_cache: dict[str, BackgroundReference] = {}

        self._build_caches()

    @classmethod
    def get_instance(cls) -> "SNESSceneEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _build_caches(self):
        """Build reference caches for fast lookup."""
        for char_name, config in CHARACTER_SPRITES.items():
            rom = self.asset_extractor.find_rom(config["game"])
            if rom:
                frames = config.get("frames", 8)
                poses = self._get_character_poses(char_name)
                self._sprite_cache[char_name] = SpriteReference(
                    character=char_name,
                    game=config["game"],
                    rom_hash=rom["hash_sha256"],
                    rom_path=rom["path"],
                    bank=config["bank"],
                    offset=config["offset"],
                    frames=frames,
                    poses=poses,
                )

        for track_name, config in AUDIO_TRACKS.items():
            rom = self.asset_extractor.find_rom(config["game"])
            if rom:
                self._audio_cache[track_name] = AudioReference(
                    track_name=track_name,
                    game=config["game"],
                    addr=config["addr"],
                    audio_type=config["type"],
                    rom_hash=rom["hash_sha256"],
                )

        for genre, games in GENRE_BACKGROUNDS.items():
            for game_key, config in games.items():
                rom = self.asset_extractor.find_rom(game_key)
                if rom:
                    self._bg_cache[f"{genre}_{game_key}"] = BackgroundReference(
                        genre=genre,
                        game=game_key,
                        addr=config["addr"],
                        size=config["size"],
                        rom_hash=rom["hash_sha256"],
                    )

    def _get_character_poses(self, character: str) -> dict[str, int]:
        """Get typical animation poses for a character."""
        pose_map = {
            "mario": {"idle": 0, "walk": 1, "jump": 2, "spin": 3, "powerup": 4},
            "luigi": {"idle": 0, "walk": 1, "jump": 2, "spin": 3},
            "yoshi": {"idle": 0, "walk": 1, "jump": 2, "swallow": 3},
            "bowser": {"idle": 0, "walk": 1, "fire": 2, "laugh": 3},
            "peach": {"idle": 0, "wave": 1, "worried": 2},
            "link": {"idle": 0, "walk": 1, "attack": 2, "spin": 3},
            "zelda": {"idle": 0, "magic": 1, "help": 2},
            "ness": {"idle": 0, "walk": 1, "psi": 2},
            "fox": {"idle": 0, "fly": 1, "laser": 2, "boost": 3},
            "kirby": {"idle": 0, "walk": 1, "jump": 2, "swallow": 3, "copy": 4},
            "ryu": {"idle": 0, "walk": 1, "crouch": 2, "hadouken": 3, "shoryuken": 4},
            "ken": {"idle": 0, "walk": 1, "shoryuken": 2, "shinku": 3},
            "dk": {"idle": 0, "walk": 1, "jump": 2, "barrel": 3},
            "crono": {"idle": 0, "slash": 1, "tech": 2},
            "megaman": {"idle": 0, "walk": 1, "jump": 2, "buster": 3, "sword": 4},
        }
        return pose_map.get(character, {"idle": 0})

    def get_sprite_reference(self, character: str) -> SpriteReference:
        """Get a sprite reference for a character."""
        if character not in self._sprite_cache:
            raise ValueError(
                f"Unknown character: {character}. Available: {list(self._sprite_cache.keys())}"
            )
        return self._sprite_cache[character]

    def get_audio_reference(self, track: str) -> AudioReference:
        """Get an audio reference for a track."""
        if track not in self._audio_cache:
            raise ValueError(
                f"Unknown track: {track}. Available: {list(self._audio_cache.keys())}"
            )
        return self._audio_cache[track]

    def get_background_reference(
        self, genre: str, game: str | None = None
    ) -> BackgroundReference:
        """Get a background reference for a genre."""
        key = f"{genre}_{game}" if game else genre

        if key in self._bg_cache:
            return self._bg_cache[key]

        if genre in self._bg_cache:
            return self._bg_cache[genre]

        # Try to find ANY game with this genre
        for cache_key, bg_ref in self._bg_cache.items():
            if bg_ref.genre == genre:
                return bg_ref

        raise ValueError(
            f"Unknown background genre: {genre}. Available: {list(set(bg.genre for bg in self._bg_cache.values()))}"
        )

    def list_available_characters(self) -> list[str]:
        """List all available characters."""
        return list(self._sprite_cache.keys())

    def list_available_tracks(self) -> list[str]:
        """List all available audio tracks."""
        return list(self._audio_cache.keys())

    def list_available_backgrounds(self) -> list[str]:
        """List all available background genres."""
        return list(set(bg.genre for bg in self._bg_cache.values()))

    def list_available_games(self) -> list[str]:
        """List all games with ROM assets."""
        games = set()
        games.update(sprite.game for sprite in self._sprite_cache.values())
        games.update(audio.game for audio in self._audio_cache.values())
        return sorted(list(games))

    def get_gary_prompt(self) -> str:
        """Generate a comprehensive prompt for Gary on how to use this system."""
        return (
            """
# GARY'S SNES SCENE CREATION GUIDE

## Overview
You have access to a SNES Scene Engine that lets you programmatically create authentic 
SNES-style scenes using real game assets from the ROM library.

## Quick Start

```python
from app.snes_scene_engine import SNESSceneEngine, SceneDirector

engine = SNESSceneEngine.get_instance()
director = SceneDirector(engine)

# Create a pre-built scene
scene = director.create_scene("SUPER MARIOWORLD", "castle_confrontation")

# Or create a custom scene
scene = director.create_custom_scene(
    game="THE LEGEND OF ZELDA",
    characters=["link", "ganon"],
    background="castle",
    music="zelda_boss"
)
```

## Available Games

"""
            + ", ".join(self.list_available_games())
            + """

## Available Characters

"""
            + ", ".join(self.list_available_characters())
            + """

## Available Music Tracks

"""
            + ", ".join(self.list_available_tracks())
            + """

## Available Background Genres

"""
            + ", ".join(self.list_available_backgrounds())
            + """

## Scene Types by Game

For SUPER MARIOWORLD:
- castle_confrontation: Bowser vs Mario, dramatic showdown
- overworld_meadow: Outdoor adventure, bright and cheerful
- underground_treasure: Cave exploration, mysterious atmosphere
- airship_assault: Action sequence on Bowser's airship

For THE LEGEND OF ZELDA:
- triforce_revelation: Epic Light World temple scene
- hyrule_overworld: Top-down Hyrule Field exploration
- dungeon_exploration: Dark dungeon with torches

For EarthBound:
- boss_encounter: Full party vs enemy, turn-based battle UI
- peaceful_twoson: Town scene with NPCs

For Chrono Trigger:
- final_battle: 7-character lineup, ultimate confrontation
- ocean_palace: Underwater ruins, blue atmosphere

For other games, check director.scene_templates.list_scenes_for_game(game_name)

## Scene Modification

After creating a scene, you can modify it:

```python
# Add a character
scene.add_character("luigi", pose="jump", position=(200, 150))

# Change background
scene.set_background("desert")

# Add sound effects
scene.add_sfx("smw_coin", time=2.5)

# Swap music
scene.play_music("smw_star")
```

## Output Formats

Get the scene as:
- Gary script: scene.to_gary_script()
- API params: scene.to_api_call()

## Example: Creating a Custom TV Segment

```python
# Gary wants to create a "Retro Gaming Night" segment
scene = director.create_custom_scene(
    game="Street Fighter 2",
    characters=["ryu", "ken"],
    background="city",
    music="sf2_vs"
)

# Add dramatic SFX
scene.add_sfx("mk_round", time=0)
scene.add_sfx("smw_powerup", time=3.0)

# Gary's script for this scene:
print(scene.to_gary_script())
```

## Important Notes

1. All asset references point to real data from the 784-ROM library
2. Scene timing is based on typical SNES game pacing
3. Camera notes give guidance on authentic SNES camera angles
4. You can chain multiple scenes together for a complete show segment
5. Use the engine's list methods to discover available assets
"""
        )


if __name__ == "__main__":
    engine = SNESSceneEngine.get_instance()

    print("=" * 60)
    print("SNES SCENE ENGINE - Gary's Interface")
    print("=" * 60)

    print("\nAvailable Games:", engine.list_available_games())
    print("\nAvailable Characters:", engine.list_available_characters())
    print("\nAvailable Music:", engine.list_available_tracks())
    print("\nAvailable Backgrounds:", engine.list_available_backgrounds())

    print("\n" + "=" * 60)
    print("Creating Example Scene...")
    print("=" * 60)

    director = SceneDirector(engine)

    try:
        scene = director.create_scene("SUPER MARIOWORLD", "castle_confrontation")
        print("\n" + director.describe_scene_for_gary(scene))
        print("\n--- Gary Script ---")
        print(scene.to_gary_script())
    except ValueError as e:
        print(f"Error: {e}")
