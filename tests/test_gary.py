import json
from app.gary import Gary
from app.action_trigger import ActionTrigger
from unittest.mock import Mock, patch


@patch("langchain_openai.ChatOpenAI")
def test_gary_decision(mock_llm):
    mock_llm.return_value.invoke.return_value.content = json.dumps(
        {
            "show": "Test Show",
            "hosts": ["Crono"],
            "topic": "Time Travel",
            "actions": {
                "visual": {"bank": 0x10, "offset": "0x0000", "sprite_name": "chrono"},
                "audio": {"offset": "0x080000", "type": "brr"},
                "sync": "60fps",
            },
        }
    )
    gary = Gary(energy=3)
    decision = gary.decide_show(["Crono"], "Time Travel")
    assert "show" in decision
    assert decision["actions"]["visual"]["validated"]  # From trigger


@patch("langchain_openai.ChatOpenAI")
def test_fallback_decision(mock_llm):
    mock_llm.return_value.invoke.side_effect = Exception()
    gary = Gary(energy=3)
    decision = gary.decide_show(["Luigi"], "Plumbing")
    assert decision["show"] == "Fallback SNES Talk"
    assert "validated" in decision["actions"]["visual"]


def test_action_trigger_lookup():
    trigger = ActionTrigger()
    action = {"visual": {"bank": 0, "offset": "0x100", "sprite_name": "mario"}}
    valid = trigger.lookup_validate(action)
    assert valid  # Mock manifest has it
    assert action["validated"]


def test_execute_fallback():
    trigger = ActionTrigger()
    action = {"visual": {"bank": 999, "offset": "0xZZZ"}}
    valid = trigger.lookup_validate(action)
    assert not valid
    executed = trigger.execute({"actions": {"visual": action}})
    assert "fallback" in executed["actions"]["visual"]["sprite_name"]


# Simulate 50 decisions
def test_50_decisions():
    mock_llm = Mock()
    mock_llm.invoke.return_value.content = json.dumps(
        {"show": "Mock", "actions": {"visual": {"bank": 0, "offset": "0x100"}}}
    )
    with patch("langchain_openai.ChatOpenAI", return_value=mock_llm):
        gary = Gary()
        valid_count = 0
        for i in range(50):
            decision = gary.decide_show(["Host"], f"Topic {i}")
            if all(
                a.get("validated", False) for a in decision.get("actions", {}).values()
            ):
                valid_count += 1
        assert valid_count == 50  # 100% valid
