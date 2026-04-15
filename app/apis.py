import random
from datetime import datetime


def get_twitch_metrics(channel: str = "t3mplate_tv") -> dict:
    """Fetch Twitch viewers/chat (mock for Gary)."""
    # Real: https://api.twitch.tv/helix/streams?user_login=t3mplate_tv
    return {
        "viewers": random.randint(50, 500),
        "chat_rate": 10,
        "top_emote": "PogChamp",
    }


def get_news_trends(top_n: int = 5) -> list[str]:
    """Fetch news headlines for topics (mock RSS)."""
    # Real: NewsAPI or RSS SNES/gaming
    return [
        "SNES remakes trending",
        "Chrono Trigger HD rumors",
        "RetroArch Lutro update",
    ]


def get_twitch_webhook(event: str) -> dict:
    """Webhook for real-time metrics."""
    return {"event": event, "timestamp": datetime.now().isoformat()}


__all__ = ["get_twitch_metrics", "get_news_trends", "get_twitch_webhook"]
