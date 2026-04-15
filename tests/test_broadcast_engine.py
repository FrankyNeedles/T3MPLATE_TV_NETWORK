"""
Tests for Broadcast Engine - 90s TV broadcast elements.
"""

from app.broadcast_engine import (
    BroadcastDirector,
    LowerThird,
    NewsTicker,
    BreakingNewsBanner,
    StationID,
    TVRating,
    ShowBumper,
    CommercialBreakCard,
    ComingUpNext,
    ColorBars,
    PublicServiceAnnouncement,
    BroadcastSegment,
    TickerStyle,
    create_news_broadcast,
    create_talk_show,
    create_commercial_break,
)


class TestBroadcastElements:
    """Test 90s TV broadcast elements."""

    def test_lower_third(self):
        lt = LowerThird(name="Mario", title="Anchor")
        assert lt.name == "Mario"
        assert lt.title == "Anchor"
        assert lt.style == "classic"

        cmd = lt.to_gary_command()
        assert "LOWER_THIRD" in cmd
        assert "Mario" in cmd
        assert "Anchor" in cmd

    def test_news_ticker(self):
        ticker = NewsTicker(
            headlines=["Breaking news!", "More at 11"], style=TickerStyle.CLASSIC
        )
        assert len(ticker.headlines) == 2

        cmd = ticker.to_gary_command()
        assert "TICKER" in cmd

    def test_breaking_news_banner(self):
        banner = BreakingNewsBanner(text="URGENT: Big Story", flash=True)
        assert banner.text == "URGENT: Big Story"
        assert banner.flash is True

        cmd = banner.to_gary_command()
        assert "BREAKING" in cmd
        assert "flash" in cmd

    def test_station_id(self):
        sid = StationID(callsign="T3TV", network="Independent")
        assert sid.callsign == "T3TV"

        cmd = sid.to_gary_command()
        assert "STATION_ID" in cmd
        assert "T3TV" in cmd

    def test_tv_rating(self):
        rating = TVRating(rating="TV-14", content="LV")
        assert rating.rating == "TV-14"
        assert rating.content == "LV"

        cmd = rating.to_gary_command()
        assert "TV_RATING" in cmd

    def test_show_bumper(self):
        bumper = ShowBumper(
            show_name="Mushroom News", episode_title="AI Revolution", style="news"
        )
        assert bumper.show_name == "Mushroom News"

        cmd = bumper.to_gary_command()
        assert "BUMPER" in cmd
        assert "AI Revolution" in cmd

    def test_commercial_card(self):
        comm = CommercialBreakCard(card_type="local", sponsor="Pizza Tower")
        assert comm.card_type == "local"
        assert comm.sponsor == "Pizza Tower"

        cmd = comm.to_gary_command()
        assert "COMMERCIAL" in cmd

    def test_coming_up_next(self):
        cup = ComingUpNext(next_show="Weather", next_episode="Storm Watch")
        assert cup.next_show == "Weather"

        cmd = cup.to_gary_command()
        assert "COMING_UP" in cmd

    def test_color_bars(self):
        bars = ColorBars(duration_seconds=10, include_tone=True)
        assert bars.duration_seconds == 10
        assert bars.include_tone is True

        cmd = bars.to_gary_command()
        assert "COLOR_BARS" in cmd

    def test_psa(self):
        psa = PublicServiceAnnouncement(topic="Just Say No", agency="D.A.R.E.")
        assert psa.topic == "Just Say No"

        cmd = psa.to_gary_command()
        assert "PSA" in cmd


class TestBroadcastDirector:
    """Test the broadcast director."""

    def test_create_news_broadcast(self):
        director = BroadcastDirector()
        segment = director.create_news_broadcast(
            show_name="Mushroom News",
            headlines=["Breaking", "More", "Weather"],
            anchor_name="Mario",
        )

        assert segment.segment_type == "news_broadcast"
        assert segment.lower_thirds is not None
        assert len(segment.lower_thirds) > 0
        assert segment.lower_thirds[0].name == "Mario"

    def test_create_talk_show(self):
        director = BroadcastDirector()
        segment = director.create_talk_show(
            show_name="Koopa Talk", host="Bowser", guest="Yoshi", topic="Climate Change"
        )

        assert segment.segment_type == "talk_show"
        assert len(segment.lower_thirds) == 2

    def test_create_commercial_break(self):
        director = BroadcastDirector()
        segment = director.create_commercial_break(break_type="local", has_psa=True)

        assert segment.segment_type == "commercial_break"
        assert segment.commercial is not None
        assert segment.psa is not None

    def test_create_action_scene(self):
        director = BroadcastDirector()
        segment = director.create_action_scene(
            scene_name="Fight!",
            characters=[
                {"name": "Ryu", "title": "Fighter"},
                {"name": "Ken", "title": "Challenger"},
            ],
            music="sf2_vs",
        )

        assert segment.segment_type == "action_scene"
        assert len(segment.lower_thirds) == 2


class TestBroadcastSegment:
    """Test complete broadcast segments."""

    def test_segment_to_script(self):
        segment = BroadcastSegment(
            segment_id="test_news",
            segment_type="news",
            duration=120.0,
            show_bumper=ShowBumper(show_name="Test News"),
            lower_thirds=[LowerThird(name="Mario", title="Anchor")],
            ticker=NewsTicker(headlines=["Breaking"]),
        )

        script = segment.to_gary_script()
        assert "SEGMENT: test_news" in script
        assert "BUMPER" in script
        assert "LOWER_THIRD" in script
        assert "TICKER" in script
        assert "END_SEGMENT" in script


class TestHelperFunctions:
    """Test module helper functions."""

    def test_create_news_broadcast_helper(self):
        segment = create_news_broadcast(
            show_name="Test News",
            headlines=["Headline 1", "Headline 2"],
            anchor="Mario",
        )

        assert segment is not None
        assert segment.segment_type == "news_broadcast"

    def test_create_talk_show_helper(self):
        segment = create_talk_show(
            show_name="Test Talk", host="Peach", guest="Zelda", topic="Gaming"
        )

        assert segment is not None
        assert segment.segment_type == "talk_show"

    def test_create_commercial_break_helper(self):
        segment = create_commercial_break("national")
        assert segment is not None
        assert segment.segment_type == "commercial_break"
