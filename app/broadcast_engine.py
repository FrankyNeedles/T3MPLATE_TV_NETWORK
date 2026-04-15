"""
SNES TV Broadcast Engine - Gary's 90s TV Broadcast System

Creates authentic 90s TV broadcasts using SNES assets:
- Real 90s broadcast elements (lower thirds, tickers, color bars)
- News ticker integration
- Show bumpers and station IDs
- Lower thirds for character names
- Breaking news banners
- TV ratings and V-chips
- Commercial break cards
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import random


class BroadcastElement(Enum):
    """90s TV broadcast graphic elements."""

    COLOR_BARS = "color_bars"
    STATION_ID = "station_id"
    LOWER_THIRD = "lower_third"
    NEWS_TICKER = "news_ticker"
    BREAKING_NEWS = "breaking_news"
    WEATHER_BUG = "weather_bug"
    TV_RATING = "tv_rating"
    CLOSED_CAPTION = "closed_caption"
    NETWORK_LOGO = "network_logo"
    PROGRAM_TITLE = "program_title"
    COMMERCIAL_CARD = "commercial_card"
    PUBLIC_SERVICE = "public_service"
    COMING_UP_NEXT = "coming_up_next"
    STINGER = "stinger"


class TickerStyle(Enum):
    """News ticker styles."""

    CLASSIC = "classic"  # White text on black
    SPORTS = "sports"  # Yellow on blue
    WEATHER = "weather"  # Blue on yellow
    BREAKING = "breaking"  # Red flashing


@dataclass
class LowerThird:
    """90s-style lower third graphic."""

    name: str
    title: str
    duration_frames: int = 180
    style: str = "classic"  # classic, news, sports
    position: tuple[int, int] = (64, 200)

    def to_gary_command(self) -> str:
        return f'LOWER_THIRD(name="{self.name}", title="{self.title}", style={self.style}, frames={self.duration_frames})'


@dataclass
class NewsTicker:
    """Scrolling news ticker."""

    headlines: list[str]
    style: TickerStyle = TickerStyle.CLASSIC
    speed: float = 30.0  # seconds to scroll
    loop: bool = True

    def to_gary_command(self) -> str:
        headlines_str = " | ".join(self.headlines)
        return f'TICKER(style={self.style.value}, speed={self.speed}s, headlines="{headlines_str}")'


@dataclass
class BreakingNewsBanner:
    """Breaking news full-width banner."""

    text: str
    scroll: bool = True
    flash: bool = False
    duration_frames: int = 300

    def to_gary_command(self) -> str:
        flags = []
        if self.scroll:
            flags.append("scroll")
        if self.flash:
            flags.append("flash")
        return f'BREAKING(text="{self.text}", {"+".join(flags)}, frames={self.duration_frames})'


@dataclass
class StationID:
    """Station identification card."""

    callsign: str = "T3TV"
    network: str = "Independent"
    location: str = "Local"
    music: str = "smw_title"
    duration_seconds: int = 5

    def to_gary_command(self) -> str:
        return f'STATION_ID(callsign="{self.callsign}", network="{self.network}", duration={self.duration_seconds}s)'


@dataclass
class TVRating:
    """TV rating card (PG, TV-14, etc.)."""

    rating: str = "TV-PG"
    content: str = "D"  # D=Dialog, L=Language, S=Sex, V=Violence, FV=Fantasy Violence
    duration_frames: int = 60

    def to_gary_command(self) -> str:
        return f'TV_RATING(rating="{self.rating}", content="{self.content}", frames={self.duration_frames})'


@dataclass
class CommercialBreakCard:
    """Commercial break interstitial card."""

    card_type: str = "local"  # local, national, promo
    sponsor: str = ""
    music: str = "smw_coin"
    duration_seconds: int = 5

    def to_gary_command(self) -> str:
        return f'COMMERCIAL(type={self.card_type}, sponsor="{self.sponsor}", duration={self.duration_seconds}s)'


@dataclass
class ComingUpNext:
    """Coming up next bumper."""

    next_show: str
    next_episode: str = ""
    characters: list[str] = field(default_factory=list)
    duration_seconds: int = 10

    def to_gary_command(self) -> str:
        chars = ", ".join(self.characters) if self.characters else ""
        return f'COMING_UP(next="{self.next_show}", episode="{self.next_episode}", chars="{chars}")'


@dataclass
class ColorBars:
    """SMPTE color bars."""

    duration_seconds: int = 10
    include_tone: bool = True

    def to_gary_command(self) -> str:
        tone = "yes" if self.include_tone else "no"
        return f"COLOR_BARS(duration={self.duration_seconds}s, tone={tone})"


@dataclass
class PublicServiceAnnouncement:
    """90s-style PSA card."""

    topic: str
    agency: str = "U.S. Government"
    duration_seconds: int = 15

    def to_gary_command(self) -> str:
        return f'PSA(topic="{self.topic}", agency="{self.agency}", duration={self.duration_seconds}s)'


@dataclass
class ShowBumper:
    """Show title card/bumper."""

    show_name: str
    episode_title: str = ""
    season: int = 1
    episode: int = 1
    style: str = "dramatic"  # dramatic, comedic, action
    music: str = "smw_title"
    duration_seconds: int = 5

    def to_gary_command(self) -> str:
        return f'BUMPER(show="{self.show_name}", episode="{self.episode_title}", style={self.style}, duration={self.duration_seconds}s)'


@dataclass
class BroadcastSegment:
    """Complete broadcast segment with all elements."""

    segment_id: str
    segment_type: str
    duration: float

    # Visual elements
    color_bars: Optional[ColorBars] = None
    station_id: Optional[StationID] = None
    show_bumper: Optional[ShowBumper] = None
    rating: Optional[TVRating] = None

    # During segment
    lower_thirds: list[LowerThird] = field(default_factory=list)
    ticker: Optional[NewsTicker] = None
    breaking_news: Optional[BreakingNewsBanner] = None

    # End of segment
    coming_up: Optional[ComingUpNext] = None
    psa: Optional[PublicServiceAnnouncement] = None
    commercial: Optional[CommercialBreakCard] = None

    def to_gary_script(self) -> str:
        lines = [
            f"# SEGMENT: {self.segment_id}",
            f"# TYPE: {self.segment_type}",
            f"# DURATION: {self.duration}s",
            "",
        ]

        if self.color_bars:
            lines.append(self.color_bars.to_gary_command())
        if self.station_id:
            lines.append(self.station_id.to_gary_command())
        if self.show_bumper:
            lines.append(self.show_bumper.to_gary_command())
        if self.rating:
            lines.append(self.rating.to_gary_command())

        for lt in self.lower_thirds:
            lines.append(lt.to_gary_command())

        if self.ticker:
            lines.append(self.ticker.to_gary_command())
        if self.breaking_news:
            lines.append(self.breaking_news.to_gary_command())

        if self.coming_up:
            lines.append(self.coming_up.to_gary_command())
        if self.psa:
            lines.append(self.psa.to_gary_command())
        if self.commercial:
            lines.append(self.commercial.to_gary_command())

        lines.append("")
        lines.append("# END_SEGMENT")
        return "\n".join(lines)


class BroadcastDirector:
    """
    Gary's interface for creating authentic 90s TV broadcasts.
    """

    STATION_IDS = {
        "T3TV": StationID(callsign="T3TV", network="Independent", location="Local"),
        "SNES1": StationID(
            callsign="SNES-1", network="The Mushroom Network", location="Koopa Kingdom"
        ),
        "GAMETV": StationID(
            callsign="GAME-TV", network="Retro Broadcasting", location="Console City"
        ),
    }

    PSA_TOPICS = [
        "Stay in School",
        "Just Say No to Drugs",
        "Friends Don't Let Friends Drink and Drive",
        "Read a Book Today",
        "Support Your Local Gaming Store",
        "Be a Good Sport",
        "Eat Your Vegetables",
        "Exercise Daily",
        "Buckle Up Safety",
        "Respect Your Elders",
    ]

    TICKER_TEMPLATES = {
        "news": [
            "Developing story: {topic} - More at 11",
            "Breaking: {topic} - Updates throughout the day",
            "Top story: {topic}",
        ],
        "weather": [
            "Weather: Clear skies, high of {temp}",
            "5-Day Forecast: {forecast}",
        ],
        "sports": [
            "Sports: {team} defeats {opponent} {score}",
            "Final Score: {score}",
        ],
    }

    def __init__(self):
        self.current_station = self.STATION_IDS["T3TV"]
        self.ticker_queue: list[NewsTicker] = []
        self.broadcast_clock = 0.0

    def set_station(self, station_key: str) -> None:
        if station_key in self.STATION_IDS:
            self.current_station = self.STATION_IDS[station_key]

    def create_news_broadcast(
        self,
        show_name: str,
        headlines: list[str],
        anchor_name: str = "Mario",
        co_anchor: Optional[str] = None,
    ) -> BroadcastSegment:
        """Create a news broadcast segment."""
        seg_id = f"news_{show_name.lower().replace(' ', '_')}"

        # Build lower thirds for anchors
        lower_thirds = [
            LowerThird(name=anchor_name, title="Anchor", duration_frames=120)
        ]
        if co_anchor:
            lower_thirds.append(
                LowerThird(name=co_anchor, title="Co-Anchor", duration_frames=120)
            )

        # Create ticker with headlines
        ticker = NewsTicker(
            headlines=headlines[:5] if len(headlines) > 5 else headlines,
            style=TickerStyle.CLASSIC,
            speed=60.0,
        )

        # News rating
        rating = TVRating(rating="TV-G", content="")

        return BroadcastSegment(
            segment_id=seg_id,
            segment_type="news_broadcast",
            duration=180.0,
            show_bumper=ShowBumper(show_name=show_name, style="news", music="ct_main"),
            rating=rating,
            lower_thirds=lower_thirds,
            ticker=ticker,
        )

    def create_talk_show(
        self,
        show_name: str,
        host: str,
        guest: str,
        topic: str,
    ) -> BroadcastSegment:
        """Create a talk show segment."""
        seg_id = f"talk_{show_name.lower().replace(' ', '_')}"

        lower_thirds = [
            LowerThird(name=host, title="Host", duration_frames=180),
            LowerThird(name=guest, title="Guest", duration_frames=180),
        ]

        rating = TVRating(rating="TV-14", content="L")

        return BroadcastSegment(
            segment_id=seg_id,
            segment_type="talk_show",
            duration=1800.0,  # 30 min
            show_bumper=ShowBumper(
                show_name=show_name,
                episode_title=topic,
                style="dramatic",
                music="smw_title",
            ),
            rating=rating,
            lower_thirds=lower_thirds,
        )

    def create_sports_segment(
        self,
        sport: str,
        teams: list[str],
        score: Optional[str] = None,
    ) -> BroadcastSegment:
        """Create a sports segment."""
        seg_id = f"sports_{sport.lower().replace(' ', '_')}"

        ticker = NewsTicker(
            headlines=[
                f"{teams[0]} vs {teams[1]} - {score}"
                if score
                else f"{teams[0]} vs {teams[1]}"
            ],
            style=TickerStyle.SPORTS,
        )

        lower_thirds = [
            LowerThird(name=teams[0], title="Home Team"),
            LowerThird(name=teams[1], title="Away Team") if len(teams) > 1 else None,
        ]
        lower_thirds = [lt for lt in lower_thirds if lt]

        return BroadcastSegment(
            segment_id=seg_id,
            segment_type="sports_update",
            duration=120.0,
            ticker=ticker,
            lower_thirds=lower_thirds,
        )

    def create_action_scene(
        self,
        scene_name: str,
        characters: list[dict],
        music: str = "sf2_vs",
        sfx: list[str] = None,
    ) -> BroadcastSegment:
        """Create an action scene (like Street Fighter confrontation)."""
        seg_id = f"action_{scene_name.lower().replace(' ', '_')}"

        lower_thirds = []
        for char in characters:
            if isinstance(char, dict):
                lower_thirds.append(
                    LowerThird(
                        name=char.get("name", "Fighter"),
                        title=char.get("title", "Challenger"),
                        style="dramatic",
                    )
                )

        rating = TVRating(rating="TV-14", content="V")

        return BroadcastSegment(
            segment_id=seg_id,
            segment_type="action_scene",
            duration=120.0,
            show_bumper=ShowBumper(show_name=scene_name, style="action", music=music),
            rating=rating,
            lower_thirds=lower_thirds,
        )

    def create_commercial_break(
        self,
        break_type: str = "local",
        sponsor: str = "",
        has_psa: bool = True,
    ) -> BroadcastSegment:
        """Create a commercial break sequence."""
        seg_id = f"commercial_{break_type}"

        segment = BroadcastSegment(
            segment_id=seg_id,
            segment_type="commercial_break",
            duration=90.0,
            commercial=CommercialBreakCard(
                card_type=break_type, sponsor=sponsor, duration_seconds=90
            ),
        )

        if has_psa:
            segment.psa = PublicServiceAnnouncement(
                topic=random.choice(self.PSA_TOPICS), duration_seconds=15
            )

        return segment

    def create_station_signoff(self) -> BroadcastSegment:
        """Create end of broadcast signoff."""
        return BroadcastSegment(
            segment_id="signoff",
            segment_type="station_signoff",
            duration=30.0,
            station_id=self.current_station,
            color_bars=ColorBars(duration_seconds=10),
        )

    def build_ticker_from_news(self, news_items: list[dict]) -> NewsTicker:
        """Build news ticker from current news items."""
        headlines = []
        for item in news_items[:5]:
            if isinstance(item, dict):
                headline = item.get(
                    "headline", item.get("title", item.get("text", "Breaking news"))
                )
                headlines.append(headline[:80])  # Max 80 chars
            else:
                headlines.append(str(item)[:80])

        return NewsTicker(
            headlines=headlines,
            style=TickerStyle.BREAKING
            if any("breaking" in h.lower() for h in headlines)
            else TickerStyle.CLASSIC,
        )


# Singleton instance
broadcast_director = BroadcastDirector()


def create_news_broadcast(
    show_name: str, headlines: list[str], anchor: str = "Mario", co_anchor: str = None
) -> BroadcastSegment:
    return broadcast_director.create_news_broadcast(
        show_name, headlines, anchor, co_anchor
    )


def create_talk_show(
    show_name: str, host: str, guest: str, topic: str
) -> BroadcastSegment:
    return broadcast_director.create_talk_show(show_name, host, guest, topic)


def create_action_scene(
    scene_name: str, characters: list[dict], music: str = "sf2_vs"
) -> BroadcastSegment:
    return broadcast_director.create_action_scene(scene_name, characters, music)


def create_commercial_break(break_type: str = "local") -> BroadcastSegment:
    return broadcast_director.create_commercial_break(break_type)


def build_ticker_from_news(news: list[dict]) -> NewsTicker:
    return broadcast_director.build_ticker_from_news(news)
