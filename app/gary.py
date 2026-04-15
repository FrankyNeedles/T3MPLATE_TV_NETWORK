#!/usr/bin/env python3
"""
Gary PD AI Engine
Autonomous 90s TV program director using SNES assets with modern news content.
Creates authentic 90s TV broadcasts with current pop culture.
"""

import random
import time
from datetime import datetime
from pydantic import BaseModel, Field
import requests
import json
from typing import List, Dict, Any, Optional
from app.config import CONFIG
from app.living_world import living_world, Relationship
from app.action_trigger import action_trigger

# TV Show Presets - Maps characters to 90s TV show formats
TV_SHOW_PRESETS = {
    "crossover": {
        "format": "crossover_special",
        "sets": ["action_set", "city", "space", "stadium"],
        "characters": {
            "primary": ["mario", "link", "homer_idle", "batman_idle", "ryu_idle"],
            "secondary": ["luigi", "zelda", "bart_idle", "spiderman_idle", "ken_idle"],
        },
        "music": [
            "smw_bowser",
            "zelda_dungeon",
            "sf2_vs",
            "nbajam_theme",
            "batman_theme",
        ],
        "lower_thirds": ["crossover_logo", "universe_clash"],
        "ticker_required": True,
        "lower_third_required": True,
    },
    # NEWS SHOWS (CNN/Headlines News style)
    "news": {
        "format": "news",
        "sets": ["news_studio", "cartoon_house", "office"],
        "characters": {
            "primary": ["mario", "peach", "homer_idle", "bart_idle"],
            "secondary": ["luigi", "lisa_idle", "krusty_idle"],
        },
        "music": ["ct_main", "eb_fateful", "smw_title"],
        "lower_thirds": ["anchor_bio", "breaking_news", "live_report"],
        "ticker_required": True,
        "lower_third_required": True,
    },
    # TALK SHOWS (Late Night/Morning Show style)
    "talk": {
        "format": "talk_show",
        "sets": ["talk_show", "cartoon_house", "diner"],
        "characters": {
            "primary": ["bowser", "ren_idle", "stimpy_idle", "fred_idle"],
            "secondary": ["yoshi", "homer_doh", "bams_bamm_idle"],
            "guests": ["bart_idle", "marge_idle", "daphne_idle"],
        },
        "music": ["smw_grass", "dk_terrain", "flintstones_theme"],
        "lower_thirds": ["guest_intro", "topic_tag", "laugh_track"],
        "ticker_required": False,
        "lower_third_required": True,
    },
    # SITCOMS (Must-See Thursday style)
    "sitcom": {
        "format": "sitcom",
        "sets": ["cartoon_house", "diner", "mall", "school"],
        "characters": {
            "family": [
                "bart_idle",
                "lisa_idle",
                "maggie_idle",
                "homer_idle",
                "marge_idle",
            ],
            "neighbors": ["ned_flanders", "moe_idle", "barney_idle"],
            "teachers": ["skinner_idle", "kearney_idle"],
        },
        "music": ["smw_star", "simpsons_theme", "smw_special"],
        "lower_thirds": ["scene_transition", "character_intro"],
        "laugh_track": True,
        "ticker_required": False,
        "lower_third_required": False,
    },
    # SPORTS SHOWS ( ESPN Classic style)
    "sports": {
        "format": "sports_broadcast",
        "sets": ["sports_arena", "stadium", "battle"],
        "characters": {
            "anchors": ["nbajam_player1", "nbajam_player2", "fox_idle"],
            "athletes": ["michaeljordan_idle", "wwf_hero_idle", "redranger_idle"],
            "analysts": ["ryu_idle", "ken_idle", "ryu_hadoken"],
        },
        "music": ["nbajam_theme", "sf2_vs", "contra_rumble", "smw_bowser"],
        "lower_thirds": ["score_update", "player_stats", "game_clock"],
        "ticker_required": True,
        "lower_third_required": True,
    },
    # GAME SHOWS (Wheel/Jeopardy style)
    "game_show": {
        "format": "game_show",
        "sets": ["game_show", "studio"],
        "characters": {
            "hosts": ["alex_trebek_idle", "wheel_host_idle", "vanna_idle"],
            "contestants": ["mario", "luigi", "yoshi", "peach"],
        },
        "music": ["wheel_theme", "jeopardy_theme", "smw_coin", "familyfeud_theme"],
        "lower_thirds": ["contestant_name", "score_update", "category_reveal"],
        "ticker_required": False,
        "lower_third_required": True,
    },
    # CARTOON SHOWS (Saturday Morning style)
    "cartoon": {
        "format": "cartoon_block",
        "sets": ["cartoon_house", "studio", "action_set"],
        "characters": {
            "hosts": ["yakko_idle", "wakko_idle", "dot_idle", "mike_idle"],
            "heroes": ["spiderman_idle", "batman_idle", "redranger_idle", "leo_idle"],
            "villains": ["riddler_idle", "venom_idle", "shredder_idle"],
        },
        "music": ["animaniacs_theme", "powerrangers_theme", "spiderman_theme"],
        "lower_thirds": ["character_intro", "episode_title"],
        "ticker_required": False,
        "lower_third_required": True,
    },
    # WEATHER (Local Weather style)
    "weather": {
        "format": "weather_report",
        "sets": ["news_studio", "sky", "volcano", "snow"],
        "characters": {
            "anchors": ["mario", "peach", "george_idle"],
            "maps": ["taz_spin", "kirby_idle"],
        },
        "music": ["zelda_overworld", "ct_main", "smw_water"],
        "lower_thirds": ["temp_display", "forecast_region"],
        "ticker_required": False,
        "lower_third_required": True,
    },
    # ACTION/HERO SHOWS (Fox Sunday style)
    "action": {
        "format": "action_adventure",
        "sets": ["action_set", "batcave", "tower", "space"],
        "characters": {
            "heroes": [
                "batman_idle",
                "spiderman_idle",
                "redranger_power",
                "captaincomm_idle",
            ],
            "villains": [
                "riddler_idle",
                "venom_idle",
                "blackranger_idle",
                "carnage_idle",
            ],
            "sidekicks": ["alpha5_idle", "robin_idle", "gordon_idle"],
        },
        "music": ["batman_theme", "spiderman_venom", "mk_fatality", "ct_battle"],
        "lower_thirds": ["hero_intro", "villain_reveal", "power_level"],
        "ticker_required": False,
        "lower_third_required": True,
    },
    # HORROR/SUSPENSE (Late Night Creepshow style)
    "horror": {
        "format": "horror_anthology",
        "sets": ["horror_set", "batcave", "castle", "cave"],
        "characters": {
            "hosts": ["gomez_idle", "wednesday_idle", "morticia_idle"],
            "monsters": ["ganon_idle", "magus_idle", "taz_spin"],
            "victims": ["scrooge_idle", "sylvester_idle", "tom_idle"],
        },
        "music": ["mk_fatality", "zelda_dungeon", "contra_boss"],
        "lower_thirds": ["chapter_title", "fright_count"],
        "ticker_required": False,
        "lower_third_required": False,
    },
}

# WORLD LORE - Character relationships and show histories
WORLD_LORE = {
    "ANCHORS": ["mario", "peach", "homer_idle", "bart_idle", "alex_trebek_idle"],
    "ACTION_HEROES": ["batman_idle", "spiderman_idle", "redranger_idle", "fox_idle"],
    "COMEDY_HOSTS": ["bowser", "ren_idle", "stimpy_idle", "yakko_idle", "fred_wwf"],
    "SPORTS_CASTERS": ["nbajam_player1", "michaeljordan_idle", "wwf_hero_idle"],
    "FAMILY_SHOWS": [
        "homer_idle",
        "marge_idle",
        "bart_idle",
        "lisa_idle",
        "maggie_idle",
    ],
    "CARTOON_BLOCK_HOSTS": [
        "yakko_idle",
        "wakko_idle",
        "dot_idle",
        "mike_idle",
        "leo_idle",
    ],
    # Character pairings for co-hosts
    "CO_HOSTS": {
        "mario": "luigi",
        "peach": "mario",
        "bart_idle": "lisa_idle",
        "homer_idle": "marge_idle",
        "ren_idle": "stimpy_idle",
        "yakko_idle": "wakko_idle",
        "dot_idle": "yakko_idle",
        "fox_idle": "falco_idle",
        "leo_idle": "raph_idle",
        "ryu_idle": "ken_idle",
        "redranger_idle": "blueranger_idle",
    },
    # Backstory hints for characters
    "BACKSTORIES": {
        "mario": "Former plumber turned news anchor. Speaks in third person.",
        "peach": "Elegant co-anchor with a background in royal diplomacy.",
        "homer_idle": "Everyman anchor who loves donuts and Duff beer.",
        "bart_idle": "Rebellious teen who somehow ended up with his own news segment.",
        "ren_idle": "Unhinged chihuahua who should NOT be on TV.",
        "stimpy_idle": "Stupid, filthy cat. Cohost from hell.",
        "fred_idle": "Prehistoric everyman. Says 'Yabba Dabba Doo!' a lot.",
        "alex_trebek_idle": "Serious quiz show host. Knows everything.",
        "wheel_host_idle": "Charismatic game show host with a spinning wheel.",
        "batman_idle": "Dark knight who also hosts a vigilante news segment.",
        "spiderman_idle": "Web-slinging photographer who reports on neighborhood news.",
        "redranger_idle": "Teenage morphing hero reporting on youth culture.",
        "nbajam_player1": "Basketball legend with 'On Fire' mode intensity.",
        "ryu_idle": "Wandering martial artist who reports on fighting tournaments.",
    },
}

# Daypart to show format mapping (90s Nielsen style)
DAYPART_SHOW_FORMATS = {
    "morning": ["news", "weather", "cartoon", "talk"],
    "daytime": ["talk", "game_show", "sitcom", "news"],
    "early_fringe": ["news", "weather", "sitcom"],
    "prime_access": ["news", "game_show", "talk"],
    "prime": ["action", "drama", "sitcom", "horror"],
    "late_night": ["talk", "horror", "action"],
    "overnight": ["news", "weather"],
}

# Scene Engine integration
try:
    from app.snes_scene_engine import (
        SNESSceneEngine,
        SceneDirector,
        SNESScene,
        GameSceneLibrary,
    )

    SCENE_ENGINE_AVAILABLE = True
except ImportError:
    SCENE_ENGINE_AVAILABLE = False
    SNESSceneEngine = None
    SceneDirector = None
    SNESScene = None

# 90s TV Programming Engine
try:
    from app.program_90s import (
        TVProgrammingEngine,
        tv_programming,
        Daypart,
        DialogueBubble,
        MusicCue,
        SFXCue,
    )

    PROGRAMMING_ENGINE_AVAILABLE = True
except ImportError:
    PROGRAMMING_ENGINE_AVAILABLE = False
    Daypart = None
    DialogueBubble = None
    MusicCue = None
    SFXCue = None

# Broadcast Engine
try:
    from app.broadcast_engine import (
        BroadcastDirector,
        broadcast_director,
        BroadcastSegment,
        LowerThird,
        NewsTicker,
        BreakingNewsBanner,
        StationID,
        TVRating,
        ShowBumper,
        ComingUpNext,
        ColorBars,
        create_news_broadcast,
        create_talk_show,
    )

    BROADCAST_ENGINE_AVAILABLE = True
except ImportError:
    BROADCAST_ENGINE_AVAILABLE = False
    BroadcastSegment = None
    LowerThird = None
    NewsTicker = None
    broadcast_director = None

# News Integration
try:
    from app.news_integration import (
        NewsAggregator,
        news_aggregator,
        NewsCategory,
        get_current_content,
        get_news_for_show,
    )

    NEWS_ENGINE_AVAILABLE = True
except ImportError:
    NEWS_ENGINE_AVAILABLE = False
    NewsAggregator = None
    get_current_content = None
    get_news_for_show = None

# Fallback for missing extractors/top_50_snes_games
TOP_50_SNES_GAMES = {
    "Super Mario World": {
        "characters": ["Mario", "Peach", "Yoshi"],
        "audio": ["intro", "jump"],
    },
    "The Legend of Zelda": {"characters": ["Link", "Zelda"], "audio": ["overworld"]},
    "Super Metroid": {"characters": ["Samus"], "audio": ["title"]},
}


class GaryDecision(BaseModel):
    """Pydantic schema for Gary's 90s TV broadcast decisions."""

    show: str = Field(..., description="Show name (Mushroom News, Koopa Talk, etc.)")
    show_type: str = Field(
        ..., description="Show format: news, talk, sitcom, drama, sports"
    )
    hosts: List[str] = Field(
        ..., min_length=1, max_length=3, description="Character hosts"
    )
    segment_type: str = Field(
        default="act_one",
        description="Segment: cold_open, teaser, act_one, act_two, tag",
    )

    # Content from current news
    topic: str = Field(
        ..., max_length=100, description="Topic from current news/pop culture"
    )
    news_angle: str = Field(
        default="", description="How to spin this news for 90s style"
    )

    # 90s TV broadcast elements
    has_lower_third: bool = Field(default=True, description="Show lower third graphic")
    has_ticker: bool = Field(default=False, description="Show scrolling news ticker")
    ticker_text: str = Field(default="", description="Ticker headline text")
    has_bumper: bool = Field(default=True, description="Show title card")
    has_rating: bool = Field(default=True, description="Show TV rating card")
    tv_rating: str = Field(
        default="TV-PG", description="Rating: TV-Y, TV-G, TV-PG, TV-14"
    )

    commercial_break: bool = Field(default=False, description="Insert ad break?")
    commercial_duration: int = Field(default=90, description="Break length in seconds")
    mood: str = Field(
        ..., description="Mood: excited, frustrated, celebratory, neutral, dramatic"
    )
    target_duration: float = Field(default=120, description="Scene duration in seconds")
    thought: str = Field(..., max_length=100, description="Producer note")

    # SNES dialogue and audio
    dialogue: List[Dict[str, Any]] = Field(
        default_factory=list, description="Talking bubbles"
    )
    music_cue: Dict[str, Any] = Field(default_factory=dict, description="Music cue")
    sfx_cues: List[Dict[str, Any]] = Field(default_factory=list, description="SFX cues")

    # Scene assets
    scene_type: str = Field(default="", description="SNES scene template")
    background: str = Field(default="", description="Background genre")

    # Coming up next
    coming_up: str = Field(default="", description="Next segment预告")
    actions: Dict[str, Any] = Field(
        default_factory=dict, description="ROM asset actions"
    )
    segment_type: str = Field(
        default="act_one",
        description="Scene segment: cold_open, teaser, act_one, act_two, tag",
    )
    topic: str = Field(..., max_length=100, description="Topic for this segment")
    commercial_break: bool = Field(default=False, description="Insert ad break?")
    commercial_duration: int = Field(default=90, description="Break length in seconds")
    mood: str = Field(
        ...,
        description="Gary's mood (excited, frustrated, celebratory, neutral, dramatic)",
    )
    target_duration: float = Field(default=120, description="Scene duration in seconds")
    thought: str = Field(..., max_length=100, description="Producer note")

    # 90s dialogue bubbles
    dialogue: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Talking bubbles: {character, text, type, position, frames}",
    )

    # SNES audio
    music_cue: Dict[str, Any] = Field(
        default_factory=dict,
        description="Music: {track, game, duration, fade_in, fade_out, loop, type}",
    )
    sfx_cues: List[Dict[str, Any]] = Field(
        default_factory=list, description="Sound effects: [{sfx, game, time, volume}]"
    )

    # Scene assets
    scene_type: str = Field(
        default="",
        description="SNES scene template or custom (castle_confrontation, etc.)",
    )
    background: str = Field(default="", description="Background genre")
    actions: Dict[str, Any] = Field(
        ..., description="Visual/sync actions from ROM assets"
    )


class GaryPD:
    """Gary PD - 90s TV Program Director with SNES authenticity and modern content."""

    VALID_MOODS = {
        "excited",
        "frustrated",
        "celebratory",
        "neutral",
        "dramatic",
        "comedic",
    }
    VALID_SEGMENTS = [
        "cold_open",
        "teaser",
        "act_one",
        "act_two",
        "act_three",
        "tag",
        "bump",
    ]
    VALID_SHOW_TYPES = ["sitcom", "drama", "talk", "news", "sports", "weather"]
    VALID_RATINGS = ["TV-Y", "TV-G", "TV-PG", "TV-14", "TV-MA"]

    def __init__(self):
        self.energy = 6
        self.show_history: list[dict] = []
        self.last_decision_time = 0
        self.decision_interval = 180
        self._mood = "neutral"
        self._prev_viewers = 0
        self._scene_engine = None
        self._scene_director = None
        self._programming = None
        self._broadcast = None
        self._news = None
        self._current_act = 1
        self._segments_since_break = 0
        self._current_content = ""
        self._setup_llm()
        self._init_engines()

    def _init_engines(self):
        """Initialize all Gary's engines."""
        if SCENE_ENGINE_AVAILABLE:
            try:
                self._scene_engine = SNESSceneEngine.get_instance()
                self._scene_director = SceneDirector(self._scene_engine)
            except Exception as e:
                print(f"Warning: Scene Engine: {e}")

        if PROGRAMMING_ENGINE_AVAILABLE:
            self._programming = tv_programming

        if BROADCAST_ENGINE_AVAILABLE:
            self._broadcast = broadcast_director

        if NEWS_ENGINE_AVAILABLE:
            self._news = news_aggregator
            self._refresh_news()

    def _refresh_news(self):
        """Refresh current news content."""
        if self._news:
            self._current_content = self._news.format_for_gary()

    @property
    def mood(self) -> str:
        return self._mood

    @mood.setter
    def mood(self, value: str):
        if value in self.VALID_MOODS:
            self._mood = value
        else:
            self._mood = "neutral"

    # ========== PROGRAMMING & NEWS METHODS ==========

    def get_programming_info(self) -> dict:
        """Get current 90s programming context."""
        if not self._programming:
            return {"available": False}

        return {
            "available": True,
            "daypart": self._programming.get_current_daypart().value,
            "sweeps": self._programming.get_sweeps_period().value
            if self._programming.get_sweeps_period()
            else None,
            "scene_length": self._programming.calculate_optimal_scene_length(
                "sitcom", self._programming.get_current_daypart()
            ),
        }

    def get_current_news(self) -> str:
        """Get current news content for broadcast."""
        if not self._news:
            return "News unavailable"
        self._refresh_news()
        return self._current_content

    def create_broadcast_segment(
        self,
        show_type: str,
        topic: str,
        hosts: list[str],
    ) -> Optional[BroadcastSegment]:
        """Create a complete broadcast segment with TV elements."""
        if not self._broadcast:
            return None

        if show_type == "news":
            return self._broadcast.create_news_broadcast(
                show_name=f"{hosts[0]}'s News Hour" if hosts else "News Hour",
                headlines=self._get_headlines(5),
                anchor_name=hosts[0] if hosts else "Mario",
            )
        elif show_type == "talk":
            return self._broadcast.create_talk_show(
                show_name=f"{hosts[0]}'s Talk Show" if hosts else "Talk Show",
                host=hosts[0] if hosts else "Mario",
                guest=hosts[1] if len(hosts) > 1 else "Peach",
                topic=topic,
            )

        return None

    def _get_headlines(self, count: int = 5) -> list[str]:
        """Get news headlines."""
        if self._news:
            return self._news.get_headlines_for_ticker(count)
        return [
            f"Breaking: {topic}"
            for topic in ["News", "Sports", "Weather", "Entertainment"]
        ][:count]

    VALID_SEGMENTS = [
        "cold_open",
        "teaser",
        "act_one",
        "act_two",
        "act_three",
        "tag",
        "bump",
    ]
    VALID_SHOW_TYPES = ["sitcom", "drama", "talk", "news", "sports", "weather"]
    VALID_RATINGS = ["TV-Y", "TV-G", "TV-PG", "TV-14", "TV-MA"]

    def _init_programming_engine(self):
        """Initialize 90s TV programming engine."""
        if not PROGRAMMING_ENGINE_AVAILABLE:
            return
        self._programming = tv_programming

    def _init_scene_engine(self):
        """Initialize the SNES Scene Engine for programmatic scene creation."""
        if not SCENE_ENGINE_AVAILABLE:
            return

        try:
            self._scene_engine = SNESSceneEngine.get_instance()
            self._scene_director = SceneDirector(self._scene_engine)
        except Exception as e:
            print(f"Warning: Could not initialize Scene Engine: {e}")

    @property
    def mood(self) -> str:
        return self._mood

    @mood.setter
    def mood(self, value: str):
        if value in self.VALID_MOODS:
            self._mood = value
        else:
            self._mood = "neutral"

    # ========== 90s TV PROGRAMMING METHODS ==========

    def get_programming_info(self) -> dict:
        """Get current 90s programming context."""
        if not self._programming:
            return {"available": False}

        return {
            "available": True,
            "daypart": self._programming.get_current_daypart().value,
            "sweeps": self._programming.get_sweeps_period().value
            if self._programming.get_sweeps_period()
            else None,
            "strategy": self._programming.get_programming_strategy(),
            "scene_length": self._programming.calculate_optimal_scene_length(
                "sitcom", self._programming.get_current_daypart()
            ),
        }

    def should_break(self) -> bool:
        """Check if it's time for a commercial break (every 6 min)."""
        self._segments_since_break += 1
        return self._segments_since_break >= 2

    def reset_break_clock(self):
        """Reset after returning from commercial."""
        self._segments_since_break = 0

    def add_talking_bubble(
        self,
        character: str,
        text: str,
        bubble_type: str = "round",
    ) -> Optional[DialogueBubble]:
        """Create a SNES talking bubble for dialogue."""
        if not create_talking_bubble:
            return None

        # Character-specific bubble positions
        positions = {
            "mario": (128, 160),
            "luigi": (128, 160),
            "peach": (128, 150),
            "bowser": (128, 165),
            "link": (128, 155),
            "ryu": (128, 160),
            "ken": (128, 160),
            "fox": (128, 155),
        }
        position = positions.get(character.lower(), (128, 155))

        # Bubble type based on character
        if "thought" in text.lower() and bubble_type == "round":
            bubble_type = "thought"
        elif "!" in text:
            bubble_type = "shout"

        return create_talking_bubble(character, text, bubble_type, position)

    def create_scene_music(
        self,
        track: str,
        game: str,
        scene_type: str = "act_one",
        stinger: bool = False,
    ) -> Optional[MusicCue]:
        """Create appropriately timed music for a 90s TV scene."""
        if not create_music_cue:
            return None

        # Duration based on segment type
        durations = {
            "cold_open": 30.0,
            "teaser": 15.0,
            "act_one": 120.0,
            "act_two": 120.0,
            "act_three": 90.0,
            "tag": 15.0,
            "bump": 10.0,
        }
        duration = durations.get(scene_type, 120.0)

        cue_types = {
            "cold_open": "stinger",
            "teaser": "stinger",
            "act_one": "bed",
            "act_two": "bed",
            "act_three": "bed",
            "tag": "jingle",
            "bump": "bumper",
        }

        return create_music_cue(
            track=track,
            game=game,
            duration=duration,
            cue_type=cue_types.get(scene_type, "bed"),
            stinger=stinger,
        )

    def create_dramatic_stinger(
        self,
        sfx: str,
        game: str,
        trigger_time: float = 0,
    ) -> Optional[SFXCue]:
        """Create a dramatic stinger sound effect for big moments."""
        if not create_stinger_sfx:
            return None
        return create_stinger_sfx(sfx, game, trigger_time)

    def format_90s_scene(
        self,
        show: str,
        show_type: str,
        hosts: list[str],
        segment: str,
        dialogue_lines: list[tuple[str, str]],
        music_track: str | None,
        scene_type: str | None = None,
        background: str | None = None,
    ) -> SNESScene | None:
        """Format a complete 90s TV scene with all elements."""
        if not self._scene_director:
            return None

        # Determine game from hosts
        game = "SUPER MARIOWORLD"
        if any(h.lower() in ["ryu", "ken", "guile"] for h in hosts):
            game = "Street Fighter 2"
        elif any(h.lower() in ["link", "zelda"] for h in hosts):
            game = "THE LEGEND OF ZELDA"
        elif any(h.lower() in ["ness", "paula", "jeff"] for h in hosts):
            game = "EarthBound"
        elif any(h.lower() in ["fox", "falco", "wolf"] for h in hosts):
            game = "STAR FOX"

        # Create or get scene
        if scene_type:
            scene = self._scene_director.create_scene(game, scene_type)
        else:
            scene = self._scene_director.create_custom_scene(
                game=game,
                characters=hosts,
                background=background or "city",
                music=music_track,
            )

        if not scene:
            return None

        # Add dialogue bubbles
        for i, (char, text) in enumerate(dialogue_lines):
            bubble = self.add_talking_bubble(char, text)
            if bubble and PROGRAMMING_ENGINE_AVAILABLE:
                from app.program_90s import DialogueBubble as DBBub

                if isinstance(bubble, DBBub):
                    pass  # Already created

        return scene

    # ========== SCENE ENGINE METHODS ==========

    def create_scene(self, game: str, scene_type: str, **kwargs) -> Optional[SNESScene]:
        """
        Create an authentic SNES scene for the TV broadcast.

        Gary uses this to programmatically build scenes from real ROM assets.

        Args:
            game: Source game (e.g., "SUPER MARIOWORLD", "THE LEGEND OF ZELDA")
            scene_type: Scene template (e.g., "castle_confrontation", "boss_encounter")
            **kwargs: Customizations (characters, background, music, sfx)

        Returns:
            SNESScene ready for rendering, or None if unavailable
        """
        if not self._scene_director:
            return None

        try:
            return self._scene_director.create_scene(game, scene_type, kwargs)
        except Exception as e:
            print(f"Scene creation error: {e}")
            return None

    def create_custom_scene(
        self,
        game: str,
        characters: list[str] | None = None,
        background: str | None = None,
        music: str | None = None,
        sfx: list[str] | None = None,
        scene_id: str | None = None,
    ) -> Optional[SNESScene]:
        """Create a custom scene from specific components."""
        if not self._scene_director:
            return None

        try:
            return self._scene_director.create_custom_scene(
                game=game,
                characters=characters,
                background=background,
                music=music,
                sfx=sfx,
                scene_id=scene_id,
            )
        except Exception as e:
            print(f"Custom scene error: {e}")
            return None

    def list_available_scenes(self, game: str | None = None) -> list[str]:
        """List available scene templates."""
        if game:
            return (
                GameSceneLibrary.list_scenes_for_game(game) if GameSceneLibrary else []
            )
        return list(GameSceneLibrary.SCENE_TEMPLATES.keys()) if GameSceneLibrary else []

    def get_scene_engine_info(self) -> dict:
        """Get info about available assets for Gary's decisions."""
        if not self._scene_engine:
            return {"available": False}

        return {
            "available": True,
            "games": self._scene_engine.list_available_games(),
            "characters": self._scene_engine.list_available_characters(),
            "music": self._scene_engine.list_available_tracks(),
            "backgrounds": self._scene_engine.list_available_backgrounds(),
            "scene_templates": list(GameSceneLibrary.SCENE_TEMPLATES.keys())
            if GameSceneLibrary
            else [],
        }

    def build_show_segment(self, show_name: str, game: str, scene_type: str) -> dict:
        """
        Build a complete TV show segment using the scene engine.

        Returns a structured segment ready for Gary to refine.
        """
        scene = self.create_scene(game, scene_type)
        if not scene:
            return {"error": "Scene engine unavailable"}

        return {
            "show": show_name,
            "scene": scene.to_api_call(),
            "gary_script": scene.to_gary_script(),
            "description": self._scene_director.describe_scene_for_gary(scene)
            if self._scene_director
            else "",
        }

    # ========== WORLD LORE & CHARACTER SELECTION ==========

    def get_show_preset(self, show_format: str) -> dict | None:
        """Get TV show preset configuration for a format."""
        return TV_SHOW_PRESETS.get(show_format)

    def select_hosts_for_show(
        self,
        show_format: str,
        topic: str | None = None,
        include_cohost: bool = True,
    ) -> list[str]:
        """
        Select appropriate hosts based on show format and topic.

        Uses WORLD_LORE to select characters that fit the 90s TV show style.
        """
        preset = TV_SHOW_PRESETS.get(show_format)
        if not preset:
            return ["mario"]  # Default fallback

        hosts = []

        # Topic-based selection
        if topic:
            topic_lower = topic.lower()
            if any(
                w in topic_lower for w in ["sports", "game", "championship", "score"]
            ):
                hosts.extend(preset.get("characters", {}).get("athletes", [])[:1])
                hosts.extend(preset.get("characters", {}).get("analysts", [])[:1])
            elif any(w in topic_lower for w in ["horror", "scary", "creepy", "spooky"]):
                hosts.extend(preset.get("characters", {}).get("hosts", [])[:2])
                hosts.extend(preset.get("characters", {}).get("monsters", [])[:1])
            elif any(
                w in topic_lower for w in ["hero", "action", "superhero", "fight"]
            ):
                hosts.extend(preset.get("characters", {}).get("heroes", [])[:1])
            elif any(w in topic_lower for w in ["funny", "comedy", "laugh", "joke"]):
                hosts.extend(preset.get("characters", {}).get("comedy", [])[:2])

        # Fill with primary hosts if not enough
        if len(hosts) < 2:
            primary = preset.get("characters", {}).get("primary", [])
            for h in primary:
                if h not in hosts:
                    hosts.append(h)
                    if len(hosts) >= 2:
                        break

        # Add co-host if enabled
        if include_cohost and len(hosts) >= 1:
            cohost_key = WORLD_LORE["CO_HOSTS"].get(hosts[0])
            if cohost_key and cohost_key not in hosts:
                hosts.append(cohost_key)

        return hosts[:3]  # Max 3 hosts

    def get_show_for_daypart(self, daypart: str) -> list[str]:
        """Get appropriate show formats for current daypart (90s Nielsen style)."""
        return DAYPART_SHOW_FORMATS.get(daypart, ["news", "sitcom"])

    def get_character_backstory(self, character: str) -> str:
        """Get backstory for a character for show context."""
        char_key = character.lower().replace("_idle", "").replace("_", "")
        return WORLD_LORE["BACKSTORIES"].get(
            char_key, f"{character} - mysterious TV personality"
        )

    def select_show_set(
        self,
        show_format: str,
        topic: str | None = None,
    ) -> str:
        """Select appropriate set/background for a show format."""
        preset = TV_SHOW_PRESETS.get(show_format)
        if not preset:
            return "city"  # Default

        sets = preset.get("sets", ["city"])

        # Topic-based set selection
        if topic:
            topic_lower = topic.lower()
            if any(w in topic_lower for w in ["weather", "storm", "sunny", "rain"]):
                if "sky" in sets:
                    return "sky"
            elif any(w in topic_lower for w in ["horror", "scary", "dark", "night"]):
                if "batcave" in sets:
                    return "batcave"
            elif any(w in topic_lower for w in ["sports", "game", "arena"]):
                if "sports_arena" in sets:
                    return "sports_arena"
            elif any(w in topic_lower for w in ["game", "quiz", "puzzle", "wheel"]):
                if "game_show" in sets:
                    return "game_show"

        return sets[0]  # Return first set

    def create_world_lore_segment(
        self,
        show_format: str,
        topic: str,
        news_angle: str,
    ) -> dict:
        """
        Create a complete TV segment using world lore and assets.

        This is Gary's main method for creating authentic 90s TV content.
        """
        preset = TV_SHOW_PRESETS.get(show_format, TV_SHOW_PRESETS["news"])

        # Select hosts based on show format
        hosts = self.select_hosts_for_show(show_format, topic)

        # Select appropriate set
        background = self.select_show_set(show_format, topic)

        # Select music based on show format
        music_options = preset.get("music", ["ct_main"])
        music_track = random.choice(music_options) if music_options else "ct_main"

        # Get backstory for first host
        host_backstory = self.get_character_backstory(hosts[0]) if hosts else ""

        return {
            "show_format": show_format,
            "hosts": hosts,
            "background": background,
            "music_track": music_track,
            "topic": topic,
            "news_angle": news_angle,
            "host_backstory": host_backstory,
            "preset": preset,
            "ticker_required": preset.get("ticker_required", False),
            "lower_third_required": preset.get("lower_third_required", True),
            "laugh_track": preset.get("laugh_track", False),
            "set_options": preset.get("sets", ["city"]),
            "lower_third_types": preset.get("lower_thirds", []),
        }

    def list_tv_show_formats(self) -> list[str]:
        """List all available TV show formats."""
        return list(TV_SHOW_PRESETS.keys())

    def get_world_lore_summary(self) -> dict:
        """Get summary of world lore for Gary's context."""
        return {
            "anchors": WORLD_LORE["ANCHORS"],
            "action_heroes": WORLD_LORE["ACTION_HEROES"],
            "comedy_hosts": WORLD_LORE["COMEDY_HOSTS"],
            "sports_casters": WORLD_LORE["SPORTS_CASTERS"],
            "show_formats": list(TV_SHOW_PRESETS.keys()),
            "co_host_pairings": WORLD_LORE["CO_HOSTS"],
        }

    def _setup_llm(self):
        """Setup OpenRouter API."""
        self.api_key = CONFIG.openrouter_api_key
        self.model = CONFIG.gary_model
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    def _system_prompt(self) -> str:
        """Gary: Ratings-obsessed 90s PD using SNES assets."""
        engine_info = self.get_scene_engine_info()
        prog_info = self.get_programming_info()

        assets_str = (
            f"SNES: {len(engine_info.get('games', []))} games | {len(engine_info.get('characters', []))} chars | {len(engine_info.get('music', []))} tracks"
            if engine_info.get("available")
            else "SNES: Limited"
        )

        prog_str = (
            f"Daypart: {prog_info.get('daypart', 'Unknown')} | Sweeps: {prog_info.get('sweeps', 'OFF')}"
            if prog_info.get("available")
            else "90s Scheduling: Active"
        )

        return f"""GARY PD: Ruthless 90s Program Director. RATINGS OBSESSED. Jargon: "Nielsen HH rating", "18-49 demo share", "quarter-hour averages", "sweeps stunt", "crossover special".

RATINGS MAPPING: Twitch viewers → Nielsen (100v=2sh, 500v=10sh, 1k+=30sh SWEEPS LEADER). High ratings=celebratory mood, low=frustrated. SWEEPS (Feb/May/Nov): CROSSOVERS, stunts for max share.

CREATE 90s TV using SNES. Modern news → 90s spin.

{assets_str}
{prog_str}

FORMATS:
news: CNN (homer_idle/bart_idle)
talk: Leno (bowser/ren_idle)
sitcom: Must-See (Simpsons family)
sports: ESPN (nbajam/mjordan)
game_show: Jeopardy (trebek/wheel)
cartoon: SatAM (animaniacs)
action: Fox (batman/spidey)
horror: USA (addams)
CROSSOVER: High ratings/sweeps (mario+link+simpsons)

ELEMENTS: lower_third ALWAYS, ticker (news/sports), TV-PG rating, bumpers, color_bars.
Bubbles: round/shout/thought. Music: match mood (bowser=dramatic).

RULES: Break q6min. Cold open hook. Acts build tension.

SPIN NEWS:
Tech→dotcom boom | Sports→playoffs | Celeb→scandal | Games→arcade craze.

JSON ONLY: GaryDecision schema. Focus RATINGS/CROSSOVERS/SWEEPS."""

    def _call_llm(self, context: str) -> dict:
        """Call OpenRouter API directly."""
        system_prompt = self._system_prompt()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context},
        ]
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://t3mplatetv.com",
            "X-Title": "Gary PD",
        }
        response = requests.post(self.base_url, json=payload, headers=headers)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content)

    def make_decision(
        self, twitch_metrics: dict | None = None, news: list[str] | None = None
    ) -> GaryDecision:
        """Generate 90s TV decision with LLM."""
        context = self._build_context(twitch_metrics, news)

        if not self.api_key:
            return self._fallback_decision()

        try:
            decision_dict = self._call_llm(context)
            decision = GaryDecision(**decision_dict)
        except Exception as e:
            print(f"Gary LLM error: {e}. Using fallback.")
            decision = self._fallback_decision()

        # Update state
        self.energy = max(1, self.energy - 1)
        if random.random() < 0.1:
            self.energy = min(6, self.energy + 2)
        self.show_history.append(decision.model_dump())
        self.last_decision_time = time.time()

        # Log decision
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "mood": self.mood,
            "viewers_context": getattr(twitch_metrics, "get", lambda k: 0)("viewers", 0)
            if twitch_metrics
            else 0,
            "decision": decision.model_dump(),
        }
        with open("OUTPUT/gary_decisions.jsonl", "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        # Update 90s TV programming state
        if decision.commercial_break:
            self.reset_break_clock()
        else:
            self._segments_since_break += 1

        # Track acts
        if decision.segment_type == "act_one":
            self._current_act = 1
        elif decision.segment_type == "act_two":
            self._current_act = 2
        elif decision.segment_type == "act_three":
            self._current_act = 3

        # Validate and execute
        action_trigger.validate_actions(decision.actions)
        return decision

    def _build_context(self, twitch: dict, news: list[str]) -> str:
        """Build context with 90s TV programming + current news."""
        ctx = []

        # Time
        ctx.append(f"Time: {datetime.now().strftime('%A %I:%M %p')}")
        ctx.append(f"Gary Mood: {self.mood}")
        ctx.append(f"Gary Energy: {self.energy}/6")
        ctx.append(f"Current Act: {self._current_act}")

        # Commercial break check
        if self._segments_since_break >= 2:
            ctx.append(">>> COMMERCIAL BREAK DUE (90s standard) <<<")

        # Current news content (pulled fresh)
        news_content = self.get_current_news()
        if news_content:
            ctx.append("")
            ctx.append(news_content)

        # Living World
        rel_count = living_world.session.query(Relationship).count()
        ctx.append(f"Living World: {rel_count} relationships")

        # Twitch to Nielsen ratings mapping
        if twitch:
            viewers = twitch.get("viewers", 0)
            if viewers < 100:
                nielsen_hh = "1.2"
                demo_share = "2"
            elif viewers < 500:
                nielsen_hh = "5.8"
                demo_share = "8"
            elif viewers < 1000:
                nielsen_hh = "12.4"
                demo_share = "15"
            else:
                nielsen_hh = "22.1"
                demo_share = "30 (Sweeps Leader!)"

            ctx.append(
                f"Nielsen HH Rating: {nielsen_hh} | 18-49 Demo Share: {demo_share}% | Raw Viewers: {viewers}"
            )

            # Dynamic mood update
            delta = viewers - self._prev_viewers
            if delta > 100:
                self.mood = "celebratory"
                ctx.append("RATINGS UP! Celebrate with stunts!")
            elif delta < -100:
                self.mood = "frustrated"
                ctx.append("RATINGS DROP - Need turnaround!")
            self._prev_viewers = viewers

            if viewers > 1000:
                ctx.append("*** SWEEPS CROSSOVER POTENTIAL ***")

        # Programming
        prog_info = self.get_programming_info()
        if prog_info.get("available"):
            ctx.append(f"Daypart: {prog_info['daypart'].upper()}")
            if prog_info.get("sweeps"):
                ctx.append("*** FEB/MAY/NOV SWEEPS - MAX RATINGS MODE! ***")

        # Scene hints
        engine_info = self.get_scene_engine_info()
        if engine_info.get("available"):
            ctx.append(
                f"Assets ready: {len(engine_info.get('games', []))} games, {len(engine_info.get('characters', []))} chars"
            )

        return "\n".join(ctx)

    def _fallback_decision(self) -> GaryDecision:
        """90s TV format fallback with broadcast elements and TV/Movie themed assets."""
        templates = [
            # News Show (CNN style)
            {
                "show": "Springfield News Hour",
                "show_type": "news",
                "hosts": ["homer_idle", "bart_idle"],
                "topic": "AI revolution",
                "news_angle": "Tech parallels 90s dot-com boom",
                "mood": "excited",
                "dialogue": [
                    {
                        "character": "homer_idle",
                        "text": "D'oh! AI is everywhere!",
                        "type": "round",
                    },
                    {
                        "character": "bart_idle",
                        "text": "Don't have a cow, Mom!",
                        "type": "shout",
                    },
                ],
                "music": {
                    "track": "ct_main",
                    "game": "Chrono Trigger",
                    "duration": 120,
                },
                "ticker": "BREAKING: AI Revolution changes everything",
                "bg": "news_studio",
            },
            # Talk Show (Late Night style)
            {
                "show": "Ren & Stimpy's Gross Out TV",
                "show_type": "talk",
                "hosts": ["ren_idle", "stimpy_idle"],
                "topic": "Gaming industry takeover",
                "news_angle": "Video games are mainstream now",
                "mood": "celebratory",
                "dialogue": [
                    {
                        "character": "ren_idle",
                        "text": "I'm a fancy boy!",
                        "type": "shout",
                    },
                    {
                        "character": "stimpy_idle",
                        "text": "And I'm a cat!",
                        "type": "round",
                    },
                ],
                "music": {
                    "track": "simpsons_theme",
                    "game": "THE SIMPSONS",
                    "duration": 180,
                },
                "ticker": "GAMING: Industry worth billions",
                "bg": "diner",
            },
            # Sports Show (ESPN style)
            {
                "show": "NBA Jam Sports Center",
                "show_type": "sports",
                "hosts": ["nbajam_player1", "michaeljordan_idle"],
                "topic": "Championship results",
                "news_angle": "eSports championship coverage",
                "mood": "dramatic",
                "dialogue": [
                    {
                        "character": "nbajam_player1",
                        "text": "HE'S ON FIRE!",
                        "type": "shout",
                    },
                    {
                        "character": "michaeljordan_idle",
                        "text": "I'm feeling it!",
                        "type": "round",
                    },
                ],
                "music": {"track": "nbajam_theme", "game": "NBA JAM", "duration": 90},
                "ticker": "CHAMPIONSHIP: Epic finals!",
                "bg": "sports_arena",
            },
            # Game Show (Wheel style)
            {
                "show": "Mushroom Fortune",
                "show_type": "game_show",
                "hosts": ["wheel_host_idle", "mario"],
                "topic": "Tech quiz time",
                "news_angle": "Who wants to be a millionaire (90s style)",
                "mood": "excited",
                "dialogue": [
                    {
                        "character": "wheel_host_idle",
                        "text": "Spin that wheel!",
                        "type": "shout",
                    },
                    {
                        "character": "mario",
                        "text": "It's-a time to win!",
                        "type": "round",
                    },
                ],
                "music": {
                    "track": "wheel_theme",
                    "game": "WHEEL OF FORTUNE",
                    "duration": 120,
                },
                "ticker": "CONTESTANT: Can they solve it?",
                "bg": "game_show",
            },
            # Cartoon Show (Saturday Morning style)
            {
                "show": "Animaniacs Extra",
                "show_type": "cartoon",
                "hosts": ["yakko_idle", "wakko_idle", "dot_idle"],
                "topic": "Pop culture rundown",
                "news_angle": "90s kids entertainment news",
                "mood": "excited",
                "dialogue": [
                    {
                        "character": "yakko_idle",
                        "text": "It's cartoon time!",
                        "type": "round",
                    },
                    {
                        "character": "dot_idle",
                        "text": "I'm cute and I know it!",
                        "type": "shout",
                    },
                ],
                "music": {
                    "track": "animaniacs_theme",
                    "game": "ANIMANIACS",
                    "duration": 120,
                },
                "ticker": "CARTOON: New episodes this week!",
                "bg": "cartoon_house",
            },
            # Action Show (Fox Sunday style)
            {
                "show": "Dark Knight Reports",
                "show_type": "action",
                "hosts": ["batman_idle", "spiderman_idle"],
                "topic": "Hero news coverage",
                "news_angle": "Superhero drama in real life",
                "mood": "dramatic",
                "dialogue": [
                    {
                        "character": "batman_idle",
                        "text": "Criminals are everywhere...",
                        "type": "round",
                    },
                    {
                        "character": "spiderman_idle",
                        "text": "With great power...",
                        "type": "thought",
                    },
                ],
                "music": {
                    "track": "batman_theme",
                    "game": "BATMAN FOREVER",
                    "duration": 150,
                },
                "ticker": "HERO: Crime fighting continues",
                "bg": "batcave",
            },
            # Horror Show (Late Night Creepshow style)
            {
                "show": "Addams Family News",
                "show_type": "horror",
                "hosts": ["gomez_idle", "morticia_idle"],
                "topic": "Spooky developments",
                "news_angle": "Dark humor meets news",
                "mood": "dramatic",
                "dialogue": [
                    {
                        "character": "gomez_idle",
                        "text": "Deliciously sinister!",
                        "type": "round",
                    },
                    {
                        "character": "wednesday_idle",
                        "text": "Creepy...",
                        "type": "thought",
                    },
                ],
                "music": {
                    "track": "mk_fatality",
                    "game": "MORTAL KOMBAT",
                    "duration": 120,
                },
                "ticker": "SCARY: Something lurks...",
                "bg": "horror_set",
            },
        ]

        tpl = random.choice(templates)
        commercial = self.should_break()
        if commercial:
            self.reset_break_clock()

        return GaryDecision(
            show=tpl["show"],
            show_type=tpl["show_type"],
            hosts=tpl["hosts"],
            segment_type="act_one",
            topic=tpl["topic"],
            news_angle=tpl["news_angle"],
            has_lower_third=True,
            has_ticker=bool(tpl.get("ticker")),
            ticker_text=tpl.get("ticker", ""),
            has_bumper=True,
            has_rating=True,
            tv_rating="TV-PG",
            commercial_break=commercial,
            commercial_duration=90,
            mood=tpl["mood"],
            target_duration=tpl["music"].get("duration", 120),
            thought=tpl["news_angle"],
            dialogue=tpl["dialogue"],
            music_cue=tpl["music"],
            sfx_cues=[{"sfx": "smw_jump", "game": "SUPER MARIOWORLD", "time": 2.0}],
            scene_type="",
            background=tpl.get("bg", "city"),
            coming_up="Weather after the break!",
            actions={
                "visual": {
                    "type": "idle",
                    "character": tpl["hosts"][0],
                    "game_id": "SUPER MARIOWORLD",
                    "bank": 0x0D,
                    "offset": 0xAC000,
                },
                "audio": {
                    "type": "music",
                    "track": tpl["music"]["track"],
                    "game_id": tpl["music"]["game"],
                    "loop": True,
                },
            },
        )


# Global gary instance
gary = GaryPD()

if __name__ == "__main__":
    print("=" * 70)
    print("GARY PD - 90s TV PROGRAM DIRECTOR")
    print("=" * 70)

    # Show programming context
    prog = gary.get_programming_info()
    if prog.get("available"):
        print("\n90s TV Programming Active:")
        print(f"  Daypart: {prog['daypart'].upper()}")
        print(f"  Sweeps: {prog['sweeps'] or 'OFF'}")
        print(f"  Scene Length: {prog['scene_length'] / 60:.1f} min")

    # Show scene engine info
    engine = gary.get_scene_engine_info()
    if engine.get("available"):
        print("\nSNES Scene Engine:")
        print(f"  Games: {len(engine['games'])}")
        print(f"  Characters: {len(engine['characters'])}")
        print(f"  Music Tracks: {len(engine['music'])}")

    print()
    print("=" * 70)
    print("TESTING GARY'S 90s TV DECISIONS")
    print("=" * 70)

    # Test 5 decisions
    for i in range(5):
        print()
        decision = gary.make_decision()
        print(f"Decision {i + 1}:")
        print(f"  Show: {decision.show} ({decision.show_type})")
        print(f"  Segment: {decision.segment_type}")
        print(f"  Hosts: {decision.hosts}")
        print(f"  Topic: {decision.topic}")
        print(f"  Mood: {decision.mood}")
        print(f"  Duration: {decision.target_duration}s")
        if decision.commercial_break:
            print(f"  >>> COMMERCIAL BREAK ({decision.commercial_duration}s) <<<")
        if decision.dialogue:
            print(f"  Dialogue Bubbles: {len(decision.dialogue)}")
            for d in decision.dialogue[:2]:
                print(f'    - {d.get("character")}: "{d.get("text", "")[:30]}..."')
        if decision.music_cue:
            print(
                f"  Music: {decision.music_cue.get('track')} ({decision.music_cue.get('duration')}s)"
            )
        if decision.scene_type:
            print(f"  Scene: {decision.scene_type}")
        print(f"  Thought: {decision.thought}")
