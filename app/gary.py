#!/usr/bin/env python3
"""
Gary PD AI Engine
Autonomous program director using LLM with authentic SNES asset awareness.
Outputs JSON decisions with traceable ROM-based actions.
"""

import random
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from .config import CONFIG
from .living_world import living_world, Relationship
from .action_trigger import action_trigger

# Fallback for missing extractors/top_50_snes_games - provide sample data
TOP_50_SNES_GAMES = {
    "Super Mario World": {
        "characters": ["Mario", "Peach", "Yoshi"],
        "audio": ["intro", "jump"],
    },
    "The Legend of Zelda": {"characters": ["Link", "Zelda"], "audio": ["overworld"]},
    "Super Metroid": {"characters": ["Samus"], "audio": ["title"]},
    # Add more as needed, or implement extractor
}


class GaryDecision(BaseModel):
    """Pydantic schema for Gary's decisions."""

    show: str = Field(..., description="Show name (news, talk, comedy)")
    hosts: List[str] = Field(
        ..., min_length=1, max_length=2, description="Character hosts"
    )
    topic: str = Field(..., max_length=100, description="Topic based on news/Twitch")
    commercial_break: bool = Field(default=False, description="Insert ads?")
    mood: str = Field(..., description="Gary's mood (optimistic, cautious)")
    thought: str = Field(..., max_length=100, description="Producer note")
    actions: Dict[str, Any] = Field(
        ..., description="Visual/audio/sync actions from assets"
    )


class GaryPD:
    def __init__(self):
        self.energy = 6  # 1-6 energy level
        self.show_history: List[Dict] = []
        self.last_decision_time = 0
        self.decision_interval = 180  # 3min

        # LLM setup (OpenRouter via OpenAI compat)
        self.llm = ChatOpenAI(
            model=CONFIG.gary_model,
            api_key=CONFIG.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.7,
        )

        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", self._system_prompt()),
                MessagesPlaceholder(variable_name="context"),
                MessagesPlaceholder(variable_name="history"),
            ]
        )

        self.parser = JsonOutputParser(pydantic_object=GaryDecision)

    def _system_prompt(self) -> str:
        """Core Gary personality prompt with asset awareness."""
        assets_summary = (
            f"Available: {len(TOP_50_SNES_GAMES)} games, 88 characters, BRR/SPC audio."
        )
        return f"""You are Gary PD, 90s TV Program Director for T3MPLATE TV NETWORK - authentic SNES broadcast.

{assets_summary}
Use ROM-traceable actions ONLY (no generated slop):
- Visual: 'type', 'character', 'game_id', 'bank' (hex/int), 'offset' ($XXXX), 'duration' (frames @60fps)
- Audio: 'track', 'game_id', 'brr_offset' ($XXXXXX), 'loop' (bool)
Examples: Mario jump bank 0x1D offset $8000 + BRR $1DF380.

Living World context included. Make decisions every 3min based on:
- Twitch viewers/mood, news trends
- Character chemistry (relationships -100:+100)
- Energy level (affects risk-taking)
- Show balance (dayparts: morning/prime/late)

Output STRICT JSON matching GaryDecision schema."""

    def make_decision(
        self, twitch_metrics: Optional[Dict] = None, news: List[str] = None
    ) -> GaryDecision:
        """Generate decision with LLM."""
        context = self._build_context(twitch_metrics, news)

        history = (
            self.show_history[-5:] if len(self.show_history) >= 5 else self.show_history
        )  # Recent history

        chain = self.prompt_template | self.llm | self.parser
        try:
            decision_dict = chain.invoke({"context": context, "history": history})
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

        # Validate and execute
        action_trigger.validate_actions(decision.actions)  # Log only
        return decision

    def _build_context(self, twitch: Dict, news: List[str]) -> str:
        """Build context string."""
        ctx = []
        ctx.append(f"Time: {datetime.now().strftime('%A %I:%M %p')}")
        ctx.append(f"Gary Energy: {self.energy}/6")
        ctx.append(
            f"Living World: {living_world.session.query(Relationship).count()} relationships"
        )

        if twitch:
            ctx.append(f"Twitch: {twitch.get('viewers', 0)} viewers")
        if news:
            ctx.append(f"News: {', '.join(news[:2])}")

        # Sample asset context
        sample_game = (
            list(TOP_50_SNES_GAMES.keys())[0] if TOP_50_SNES_GAMES else "Unknown"
        )
        ctx.append(
            f"Top Asset: {sample_game} (Mario bank 0x1D:$8000, jump BRR $1DF380)"
        )

        return "\n".join(ctx)

    def _fallback_decision(self) -> GaryDecision:
        """Deterministic fallback."""
        templates = [
            {
                "show": "Mushroom News",
                "hosts": ["Mario", "Peach"],
                "topic": "Kingdom update",
                "mood": "optimistic",
                "thought": "Safe choice",
            },
            {
                "show": "Koopa Talk",
                "hosts": ["Bowser", "Yoshi"],
                "topic": "Dino drama",
                "mood": "cautious",
                "thought": "High energy",
            },
        ]
        tpl = random.choice(templates)
        actions = {
            "visual": {
                "type": "idle",
                "character": tpl["hosts"][0],
                "game_id": "super_mario_world",
                "bank": 29,
                "offset": "$8000",
                "duration": 60,
            },
            "audio": {
                "type": "sfx",
                "track": "intro",
                "game_id": "super_mario_world",
                "brr_offset": "$1DF380",
                "loop": False,
            },
        }
        return GaryDecision(
            show=tpl["show"],
            hosts=tpl["hosts"],
            topic=tpl["topic"],
            commercial_break=random.choice([True, False]),
            mood=tpl["mood"],
            thought=tpl["thought"],
            actions=actions,
        )


# Global gary instance
gary = GaryPD()

if __name__ == "__main__":
    # Test 10 decisions
    for i in range(10):
        decision = gary.make_decision()
        print(
            f"Decision {i + 1}: {decision.show} - {decision.hosts} - {decision.actions}"
        )
