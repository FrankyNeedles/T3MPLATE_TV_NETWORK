"""
News & Pop Culture Integration for Gary PD

Provides Gary with current news, trending topics, and pop culture
to create authentic 90s-style broadcasts with modern content.
"""

import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class NewsCategory(Enum):
    BREAKING = "breaking"
    POLITICS = "politics"
    TECH = "tech"
    SPORTS = "sports"
    ENTERTAINMENT = "entertainment"
    WEATHER = "weather"
    BUSINESS = "business"
    SCIENCE = "science"
    HEALTH = "health"
    WORLD = "world"


@dataclass
class NewsItem:
    """Single news item."""

    headline: str
    category: NewsCategory
    summary: str = ""
    importance: int = 5  # 1-10
    has_video: bool = False
    related_topics: list[str] = field(default_factory=list)


@dataclass
class TrendingTopic:
    """Trending social media/pop culture topic."""

    topic: str
    platform: str = "general"
    volume: int = 100000
    sentiment: str = "neutral"  # positive, negative, neutral


@dataclass
class SportsScore:
    """Sports score update."""

    home_team: str
    away_team: str
    home_score: int
    away_score: int
    quarter: str = "Final"
    sport: str = "NBA"


@dataclass
class WeatherReport:
    """Weather report."""

    city: str = "Local"
    temp: int = 72
    condition: str = "Clear"
    forecast: str = "Sunny"


@dataclass
class TVContent:
    """Content ready for TV broadcast."""

    news_items: list[NewsItem] = field(default_factory=list)
    trending: list[TrendingTopic] = field(default_factory=list)
    scores: list[SportsScore] = field(default_factory=list)
    weather: Optional[WeatherReport] = None
    timestamp: datetime = field(default_factory=datetime.now)


class NewsAggregator:
    """
    Gary's news and content aggregation system.
    Generates 90s-style TV content from modern topics.
    """

    # 90s-style show names and formats
    SHOW_TEMPLATES = {
        "news": [
            "Mushroom News Hour",
            "Koopa Kingdom News",
            "Toadstool Today",
            "Plumber's Daily",
            "Star Fox News",
            "Pixel Press Brief",
        ],
        "talk": [
            "Late Night with Luigi",
            "The Peach Show",
            "Koopa Talk Tonight",
            "After Hours with Bowser",
            "Yoshi's Morning Chat",
        ],
        "sports": [
            "Super Smash Sports",
            "Championship Hour",
            "The Final Boss",
            "Victory Lap",
            "Tournament Time",
        ],
        "weather": [
            "Stormin' Norman",
            "Weather from Above",
            "Cloud Watch",
            "Forecast from Star Fox",
        ],
    }

    # 90s-style anchor personas
    ANCHOR_PERSONAS = {
        "mario": {
            "name": "Mario",
            "style": "enthusiastic",
            "catchphrase": "It's-a me!",
        },
        "luigi": {
            "name": "Luigi",
            "style": "serious",
            "catchphrase": "Let's get to work",
        },
        "peach": {"name": "Peach", "style": "warm", "catchphrase": "Here's the story"},
        "bowser": {"name": "Bowser", "style": "dramatic", "catchphrase": "Hehehe!"},
        "fox": {"name": "Fox McCloud", "style": "cool", "catchphrase": "Let's do this"},
        "ness": {"name": "Ness", "style": "quirky", "catchphrase": "OK!"},
        "link": {"name": "Link", "style": "heroic", "catchphrase": "Hyrule awaits"},
        "ryu": {"name": "Ryu", "style": "focused", "catchphrase": "Focus"},
    }

    def __init__(self):
        self.content_cache: Optional[TVContent] = None
        self.last_update = None

    def generate_content(self, categories: list[NewsCategory] = None) -> TVContent:
        """Generate TV content with 90s flair."""
        if categories is None:
            categories = [c for c in NewsCategory]

        content = TVContent()

        # Generate news items
        for cat in categories[:5]:
            item = self._generate_news_item(cat)
            content.news_items.append(item)

        # Generate trending topics
        for _ in range(3):
            content.trending.append(self._generate_trending())

        # Generate sports scores
        content.scores.append(self._generate_sports_score())

        # Generate weather
        content.weather = self._generate_weather()

        self.content_cache = content
        self.last_update = datetime.now()

        return content

    def _generate_news_item(self, category: NewsCategory) -> NewsItem:
        """Generate a single news item with 90s TV style."""

        templates = {
            NewsCategory.BREAKING: [
                "URGENT: {topic} - Developing Story",
                "BREAKING: {topic} - Developing",
                "ALERT: {topic} Updates Coming Up",
            ],
            NewsCategory.POLITICS: [
                "Congress debates {topic} legislation",
                "New policy on {topic} announced",
                "{topic} takes center stage in Washington",
            ],
            NewsCategory.TECH: [
                "New breakthrough in {topic}",
                "Tech giants react to {topic}",
                "{topic} revolutionizes industry",
                "Everything you need to know about {topic}",
            ],
            NewsCategory.SPORTS: [
                "{topic} dominates headlines",
                "Championship {topic} updates",
                "Star player discusses {topic}",
            ],
            NewsCategory.ENTERTAINMENT: [
                "{topic} sweeps the nation",
                "Everyone's talking about {topic}",
                "{topic} breaks records",
                "The {topic} phenomenon explained",
            ],
            NewsCategory.WEATHER: [
                "Weather alert: {topic}",
                "{topic} affects local forecasts",
                "Storm watch: {topic}",
            ],
            NewsCategory.BUSINESS: [
                "Markets react to {topic}",
                "{topic} impacts economy",
                "Business leaders on {topic}",
            ],
            NewsCategory.SCIENCE: [
                "Scientists discover {topic}",
                "{topic} breakthrough announced",
                "Research reveals {topic}",
            ],
            NewsCategory.HEALTH: [
                "New study on {topic}",
                "Health experts weigh in on {topic}",
                "{topic} prevention tips",
            ],
            NewsCategory.WORLD: [
                "Global response to {topic}",
                "International community reacts to {topic}",
                "{topic} spans continents",
            ],
        }

        # Modern topics for 90s-style reporting
        modern_topics = [
            "AI",
            "Streaming Wars",
            "Electric Vehicles",
            "Cryptocurrency",
            "Social Media",
            "Climate Tech",
            "Gaming Industry",
            "Space Travel",
            "Healthcare",
            "Remote Work",
            "Inflation",
            "Supply Chain",
            "Cybersecurity",
            "Streaming",
            "eSports",
            "Influencers",
            "VR/AR",
            "5G",
            "Cloud Computing",
            "Streaming Services",
        ]

        topic = random.choice(modern_topics)
        template = random.choice(
            templates.get(category, templates[NewsCategory.BREAKING])
        )
        headline = template.format(topic=topic)

        return NewsItem(
            headline=headline,
            category=category,
            summary=f"Full coverage of {topic} and its impact on daily life.",
            importance=random.randint(4, 10),
            has_video=random.choice([True, False]),
            related_topics=[topic, "Breaking News", "Full Report"],
        )

    def _generate_trending(self) -> TrendingTopic:
        """Generate a trending topic."""
        topics = [
            "Viral Video",
            "Celebrity News",
            "Movie Release",
            "Concert Tour",
            "Gaming Event",
            "Streamer Drama",
            "Tech Launch",
            "Fashion Trend",
            "Food Craze",
            "Meme",
            "TikTok Trend",
            "YouTube Sensation",
            "Award Show",
            "Reality TV",
            "Sports Highlight",
            "Comedy Clip",
        ]
        platforms = ["Twitter/X", "TikTok", "Instagram", "YouTube", "Twitch", "Reddit"]

        return TrendingTopic(
            topic=random.choice(topics),
            platform=random.choice(platforms),
            volume=random.randint(10000, 1000000),
            sentiment=random.choice(["positive", "neutral", "negative"]),
        )

    def _generate_sports_score(self) -> SportsScore:
        """Generate a sports score."""
        teams = [
            ("Koopa Kings", "Mushroom Stars"),
            ("Star Foxes", "Corneria United"),
            ("DK Dynasties", "Jungle Ballers"),
            ("Mushroom City", "Forest Fire"),
            ("Galaxy Knights", "Space Pilots"),
        ]
        home, away = random.choice(teams)

        return SportsScore(
            home_team=home,
            away_team=away,
            home_score=random.randint(70, 120),
            away_score=random.randint(70, 120),
            quarter="Q4" if random.random() > 0.5 else "Final",
            sport=random.choice(["NBA", "NFL", "MLB", "NHL"]),
        )

    def _generate_weather(self) -> WeatherReport:
        """Generate weather report."""
        conditions = ["Sunny", "Partly Cloudy", "Cloudy", "Rainy", "Stormy"]
        cities = ["Koopa Kingdom", "Toadstool Town", "Corneria City", "Mushroom City"]

        return WeatherReport(
            city=random.choice(cities),
            temp=random.randint(45, 90),
            condition=random.choice(conditions),
            forecast=f"{random.choice(conditions)} skies expected",
        )

    def get_headlines_for_ticker(self, count: int = 5) -> list[str]:
        """Get headlines formatted for news ticker."""
        content = self.content_cache or self.generate_content()

        headlines = []
        for item in content.news_items[:count]:
            # Truncate to 80 chars for ticker
            headline = (
                item.headline[:77] + "..." if len(item.headline) > 80 else item.headline
            )
            headlines.append(headline)

        return headlines

    def get_show_content(self, show_type: str = "news") -> dict:
        """Get content formatted for a specific show type."""
        content = self.content_cache or self.generate_content()

        return {
            "show_name": random.choice(
                self.SHOW_TEMPLATES.get(show_type, self.SHOW_TEMPLATES["news"])
            ),
            "anchor": random.choice(list(self.ANCHOR_PERSONAS.keys())),
            "headlines": [item.headline for item in content.news_items[:3]],
            "sports": [
                f"{s.home_team} {s.home_score} - {s.away_team} {s.away_score}"
                for s in content.scores[:2]
            ],
            "weather": f"{content.weather.city}: {content.weather.temp}°F, {content.weather.condition}"
            if content.weather
            else "",
            "trending": [t.topic for t in content.trending[:3]],
        }

    def format_for_gary(self) -> str:
        """Format content for Gary's LLM context."""
        content = self.content_cache or self.generate_content()

        lines = [
            "## CURRENT CONTENT (Gary's Raw Material)",
            f"Updated: {datetime.now().strftime('%I:%M %p')}",
            "",
            "### TOP HEADLINES:",
        ]

        for i, item in enumerate(content.news_items[:5], 1):
            lines.append(f"{i}. [{item.category.value.upper()}] {item.headline}")

        if content.weather:
            lines.append("")
            lines.append(
                f"### WEATHER: {content.weather.city}: {content.weather.temp}°F, {content.weather.condition}"
            )

        if content.scores:
            lines.append("")
            lines.append("### SCORES:")
            for score in content.scores[:2]:
                lines.append(
                    f"  {score.home_team} {score.home_score} - {score.away_team} {score.away_score} ({score.quarter})"
                )

        if content.trending:
            lines.append("")
            lines.append("### TRENDING:")
            for t in content.trending[:3]:
                lines.append(f"  #{t.topic} ({t.platform}, {t.volume:,} mentions)")

        return "\n".join(lines)


# Singleton instance
news_aggregator = NewsAggregator()


def get_current_content() -> str:
    """Get formatted content for Gary."""
    return news_aggregator.format_for_gary()


def get_news_for_show(show_type: str = "news") -> dict:
    """Get structured news for a show."""
    return news_aggregator.get_show_content(show_type)


def generate_broadcast_content(categories: list[NewsCategory] = None) -> TVContent:
    """Generate fresh broadcast content."""
    return news_aggregator.generate_content(categories)
