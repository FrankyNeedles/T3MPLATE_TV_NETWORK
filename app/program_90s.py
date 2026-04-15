"""
90s TV Programming Engine for Gary PD
Implements authentic 1990s TV scheduling, Nielsen ratings, and SNES audio.
"""

from dataclasses import dataclass, field
from datetime import datetime, time as dt_time
from enum import Enum
from typing import Optional


class Daypart(Enum):
    MORNING = "morning"
    DAYTIME = "daytime"
    PRIME_ACCESS = "prime_access"
    PRIME = "prime"
    LATE_FRINGE = "late"
    OVERNIGHT = "overnight"


class SweepsPeriod(Enum):
    FEBRUARY = "february"
    MAY = "may"
    NOVEMBER = "november"


class SceneSegment(Enum):
    COLD_OPEN = "cold_open"
    TEASER = "teaser"
    ACT_ONE = "act_one"
    ACT_TWO = "act_two"
    ACT_THREE = "act_three"
    TAG = "tag"
    BUMP = "bump"
    STINGER = "stinger"


@dataclass
class DialogueBubble:
    character: str
    text: str
    bubble_type: str = "round"
    position: tuple[int, int] = (128, 150)
    duration_frames: int = 90
    char_delay_ms: int = 33
    voice_bank: Optional[str] = None

    def to_gary_command(self) -> str:
        return f'BUBBLE({self.character}, "{self.text}", type={self.bubble_type}, frames={self.duration_frames})'


@dataclass
class MusicCue:
    track_name: str
    game: str
    start_time: float = 0.0
    duration: float = 30.0
    fade_in: float = 0.5
    fade_out: float = 0.5
    loop: bool = True
    stinger: bool = False
    cue_type: str = "bed"

    def to_gary_command(self) -> str:
        return (
            f"MUSIC({self.track_name}@{self.game}, {self.duration}s, loop={self.loop})"
        )


@dataclass
class SFXCue:
    sfx_name: str
    game: str
    trigger_time: float = 0.0
    volume: float = 1.0
    pan: float = 0.0

    def to_gary_command(self) -> str:
        return f"SFX({self.sfx_name}@{self.game}, {self.trigger_time}s)"


@dataclass
class CommercialBreak:
    duration_seconds: int = 90
    content_type: str = "local"
    position: str = "act_break"


@dataclass
class SceneTiming:
    segment_type: SceneSegment
    target_duration: float
    actual_duration: float = 0
    music_cues: list[MusicCue] = field(default_factory=list)
    sfx_cues: list[SFXCue] = field(default_factory=list)
    dialogue_bubbles: list[DialogueBubble] = field(default_factory=list)


@dataclass
class ShowBlock:
    name: str
    target_demographic: str = "18-49"
    days: list[str] = field(default_factory=lambda: ["Thursday"])
    timeslot: tuple[str, str] = ("8:00 PM", "11:00 PM")
    competitive_with: list[str] = field(default_factory=list)


@dataclass
class RatingsContext:
    sweeps_period: SweepsPeriod | None
    is_premiere: bool = False
    is_finale: bool = False
    is_season_finale: bool = False
    holiday_special: bool = False
    cume_viewers: int = 0
    rating: float = 0.0


class TVProgrammingEngine:
    """90s TV programming logic for Gary."""

    CONTENT_PER_HALF_HOUR = 22 * 60
    COMMERCIAL_PER_HALF_HOUR = 8 * 60
    BREAK_INTERVAL = 6 * 60

    DAYPART_SHOWS = {
        Daypart.MORNING: ["game_show", "talk", "news"],
        Daypart.DAYTIME: ["soap_opera", "talk_show", "game_show"],
        Daypart.PRIME_ACCESS: ["magazine", "news", "sports"],
        Daypart.PRIME: ["sitcom", "drama", "action"],
        Daypart.LATE_FRINGE: ["talk", "news", "comedy"],
        Daypart.OVERNIGHT: ["infomercial", "rerun"],
    }

    BLOCK_PROGRAMMING = {
        "NBC_MUST_SEE": ShowBlock(
            name="Must-See TV", days=["Thursday"], competitive_with=["CSI"]
        ),
        "ABC_TGIF": ShowBlock(
            name="TGIF", days=["Friday"], competitive_with=["Must-See TV"]
        ),
        "FOX_SUNDAY": ShowBlock(
            name="Fox Sunday", days=["Sunday"], competitive_with=["60 Minutes"]
        ),
    }

    SEGMENT_MUSIC = {
        "cold_open": [
            ("smw_title", "SUPER MARIOWORLD"),
            ("zelda_overworld", "THE LEGEND OF ZELDA"),
        ],
        "teaser": [("smw_star", "SUPER MARIOWORLD"), ("sf2_vs", "Street Fighter 2")],
        "act_one": [
            ("smw_grass", "SUPER MARIOWORLD"),
            ("dk_terrain", "DONKEY KONG COUNTRY"),
            ("ct_main", "Chrono Trigger"),
        ],
        "act_two": [("smw_castle", "SUPER MARIOWORLD"), ("eb_fateful", "EarthBound")],
        "act_three": [
            ("smw_bowser", "SUPER MARIOWORLD"),
            ("ct_battle", "Chrono Trigger"),
            ("mk_fatality", "MORTAL KOMBAT"),
        ],
        "tag": [("smw_powerup", "SUPER MARIOWORLD"), ("smw_coin", "SUPER MARIOWORLD")],
    }

    DRAMATIC_SFX = {
        "comedic": [
            ("smw_jump", "SUPER MARIOWORLD"),
            ("smw_coin", "SUPER MARIOWORLD"),
            ("smw_powerup", "SUPER MARIOWORLD"),
        ],
        "dramatic": [
            ("smw_bowser", "SUPER MARIOWORLD"),
            ("mk_fatality", "MORTAL KOMBAT"),
            ("sf2_vs", "Street Fighter 2"),
        ],
        "transition": [
            ("smw_coin", "SUPER MARIOWORLD"),
            ("smw_star", "SUPER MARIOWORLD"),
        ],
    }

    def __init__(self):
        self.current_show = None
        self.show_clock = 0.0
        self.act_clock = 0.0

    def get_current_daypart(self) -> Daypart:
        now = datetime.now()
        current_time = now.time()

        if dt_time(7, 0) <= current_time < dt_time(9, 0):
            return Daypart.MORNING
        elif dt_time(9, 0) <= current_time < dt_time(16, 0):
            return Daypart.DAYTIME
        elif dt_time(16, 0) <= current_time < dt_time(19, 0):
            return Daypart.PRIME_ACCESS
        elif dt_time(19, 0) <= current_time < dt_time(23, 0):
            return Daypart.PRIME
        elif dt_time(23, 0) <= current_time < dt_time(1, 0):
            return Daypart.LATE_FRINGE
        return Daypart.OVERNIGHT

    def get_sweeps_period(self) -> SweepsPeriod | None:
        month = datetime.now().month
        if month == 2:
            return SweepsPeriod.FEBRUARY
        elif month == 5:
            return SweepsPeriod.MAY
        elif month == 11:
            return SweepsPeriod.NOVEMBER
        return None

    def get_ratings_context(self) -> RatingsContext:
        sweeps = self.get_sweeps_period()
        month = datetime.now().month
        day = datetime.now().day

        return RatingsContext(
            sweeps_period=sweeps,
            is_premiere=month == 9 and 7 <= day <= 20,
            is_finale=month == 5 and 15 <= day <= 25,
            is_season_finale=month in [4, 5] and 18 <= day <= 25,
            holiday_special=month == 12 and 1 <= day <= 26,
        )

    def get_appropriate_show_types(self) -> list[str]:
        return self.DAYPART_SHOWS.get(self.get_current_daypart(), ["general"])

    def get_block_for_timeslot(self, day: str, hour: int) -> ShowBlock | None:
        for block in self.BLOCK_PROGRAMMING.values():
            if day in block.days and 19 <= hour < 23:
                return block
        return None

    def calculate_optimal_scene_length(self, show_type: str, daypart: Daypart) -> float:
        if daypart == Daypart.PRIME:
            if show_type == "sitcom":
                return 120.0
            elif show_type == "drama":
                return 180.0
        elif daypart == Daypart.DAYTIME:
            if show_type == "soap_opera":
                return 60.0
        return 150.0

    def get_programming_strategy(self) -> dict:
        daypart = self.get_current_daypart()
        sweeps = self.get_sweeps_period()
        block = self.get_block_for_timeslot(
            datetime.now().strftime("%A"), datetime.now().hour
        )

        return {
            "daypart": daypart.value,
            "recommended_shows": self.get_appropriate_show_types(),
            "sweeps_mode": sweeps.value if sweeps else "none",
            "commercial_interval_min": 6,
            "scene_length_optimal": self.calculate_optimal_scene_length(
                "sitcom", daypart
            ),
            "block_programming": block.name if block else None,
            "production_budget": "maximum" if sweeps else "normal",
            "special_event": sweeps is not None,
            "cross_promotion": sweeps is not None,
        }

    def format_gary_context(self) -> str:
        strategy = self.get_programming_strategy()

        lines = [
            f"Daypart: {strategy['daypart'].upper()}",
            f"Sweeps: {strategy['sweeps_mode']}",
            f"Commercial break every: {strategy['commercial_interval_min']} min",
            f"Scene target: {strategy['scene_length_optimal'] / 60:.1f} min",
        ]

        if strategy.get("special_event"):
            lines.append("SWEEPS: Maximum production!")

        return "\n".join(lines)


tv_programming = TVProgrammingEngine()


def get_programming_context() -> str:
    return tv_programming.format_gary_context()


def create_talking_bubble(
    character: str,
    text: str,
    bubble_type: str = "round",
    position: tuple[int, int] = (128, 150),
) -> DialogueBubble:
    return DialogueBubble(
        character=character, text=text, bubble_type=bubble_type, position=position
    )


def create_music_cue(
    track: str,
    game: str,
    duration: float = 30.0,
    cue_type: str = "bed",
    stinger: bool = False,
) -> MusicCue:
    return MusicCue(
        track_name=track,
        game=game,
        duration=duration,
        cue_type=cue_type,
        stinger=stinger,
    )


def create_stinger_sfx(sfx: str, game: str, trigger_time: float = 0) -> SFXCue:
    return SFXCue(sfx_name=sfx, game=game, trigger_time=trigger_time)
