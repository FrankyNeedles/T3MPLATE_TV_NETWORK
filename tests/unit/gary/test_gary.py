#!/usr/bin/env python3
"""
Gary Tests - AI Decision Engine
Tests LLM prompts, JSON parsing, fallback logic.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.gary import GaryPD, GaryDecision
from app.action_trigger import action_trigger
import json


@pytest.fixture
def mock_llm():
    """Mock LLM responses."""
    with patch("app.gary.ChatOpenAI") as mock_openai:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = json.dumps(
            {
                "show": "Test Show",
                "hosts": ["Mario", "Luigi"],
                "topic": "Test topic",
                "commercial_break": False,
                "mood": "optimistic",
                "thought": "Test thought",
                "actions": {
                    "visual": {
                        "type": "talk",
                        "character": "Mario",
                        "game_id": "smw",
                        "bank": 0x1D,
                        "offset": "$8000",
                        "duration": 120,
                    },
                    "audio": {
                        "type": "intro",
                        "track": "fanfare",
                        "game_id": "smw",
                        "brr_offset": "$1DF380",
                        "loop": False,
                    },
                },
            }
        )
        mock_openai.return_value = mock_llm
        yield mock_llm


def test_gary_decision(mock_llm):
    """Test Gary decision generation."""
    gary = GaryPD()
    decision = gary.make_decision()
    assert isinstance(decision, GaryDecision)
    assert len(decision.hosts) <= 2
    assert "actions" in decision.model_dump()


def test_fallback_decision():
    """Test fallback (no LLM)."""
    gary = GaryPD()
    decision = gary._fallback_decision()
    assert decision.show in ["Mushroom News", "Koopa Talk"]
    assert "actions" in decision.model_dump()


def test_action_trigger_validate():
    """Test validation."""
    validation = action_trigger.validate_actions(
        {
            "visual": {"game_id": "super_mario_world", "character": "mario"},
            "audio": {"game_id": "super_mario_world", "track": "jump_sfx"},
        }
    )
    assert "visual" in validation
    assert "audio" in validation


def test_execute_decision():
    """Test full execution (prints to stdout)."""
    sample = {
        "show": "Mario Talk",
        "actions": {
            "visual": {
                "character": "mario",
                "game_id": "smw",
                "bank": 29,
                "offset": "$8000",
            },
            "audio": {"track": "talk", "game_id": "smw", "brr_offset": "$1E0000"},
        },
    }
    action_trigger.execute_decision(sample)
    # Check output (console verification)


def test_50_decisions(mock_llm):
    """Milestone: 50 valid decisions."""
    gary = GaryPD()
    decisions = []
    for i in range(50):
        decision = gary.make_decision()
        decisions.append(decision)
        assert isinstance(decision, GaryDecision)
    print(
        f"✅ Milestone: 50 decisions generated ({len(set(d.show for d in decisions))} unique shows)"
    )
    assert len(decisions) == 50


if __name__ == "__main__":
    pytest.main(["-v", __file__])
