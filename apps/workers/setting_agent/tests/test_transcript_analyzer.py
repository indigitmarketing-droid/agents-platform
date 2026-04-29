import json
import pytest
from unittest.mock import MagicMock
from apps.workers.setting_agent.transcript_analyzer import (
    analyze_transcript,
    AnalysisError,
)


SAMPLE_LEAD = {
    "name": "Joe's Pizza",
    "category": "restaurant",
    "city": "Brooklyn",
}


def make_claude_returning(payload):
    client = MagicMock()
    response = MagicMock()
    text = json.dumps(payload) if isinstance(payload, dict) else payload
    response.content = [MagicMock(text=text)]
    client.messages.create = MagicMock(return_value=response)
    return client


def test_analyzes_accepted_transcript():
    client = make_claude_returning({
        "outcome": "accepted",
        "opt_out": False,
        "call_brief": {
            "custom_requests": "highlight pizza",
            "services": ["pizza", "delivery"],
            "style_preference": "modern",
            "target_audience": "families",
            "opening_hours": "11am-10pm",
        },
    })
    result = analyze_transcript("Agent: ... User: Yes...", SAMPLE_LEAD, client)
    assert result["outcome"] == "accepted"
    assert result["opt_out"] is False
    assert result["call_brief"]["services"] == ["pizza", "delivery"]


def test_analyzes_rejected_transcript():
    client = make_claude_returning({
        "outcome": "rejected",
        "opt_out": False,
        "call_brief": None,
    })
    result = analyze_transcript("User: No thanks", SAMPLE_LEAD, client)
    assert result["outcome"] == "rejected"
    assert result["call_brief"] is None


def test_detects_opt_out():
    client = make_claude_returning({
        "outcome": "rejected",
        "opt_out": True,
        "call_brief": None,
    })
    result = analyze_transcript("User: Don't call again!", SAMPLE_LEAD, client)
    assert result["opt_out"] is True


def test_handles_unclear_outcome():
    client = make_claude_returning({
        "outcome": "unclear",
        "opt_out": False,
        "call_brief": None,
    })
    result = analyze_transcript("User: Maybe later", SAMPLE_LEAD, client)
    assert result["outcome"] == "unclear"


def test_strips_markdown_code_fences():
    payload = {"outcome": "accepted", "opt_out": False, "call_brief": {}}
    client = make_claude_returning(f"```json\n{json.dumps(payload)}\n```")
    result = analyze_transcript("yes", SAMPLE_LEAD, client)
    assert result["outcome"] == "accepted"


def test_includes_lead_context_in_prompt():
    client = make_claude_returning({
        "outcome": "accepted",
        "opt_out": False,
        "call_brief": {},
    })
    analyze_transcript("foo", SAMPLE_LEAD, client)
    call_args = client.messages.create.call_args
    prompt = call_args.kwargs["messages"][0]["content"]
    assert "Joe's Pizza" in prompt
    assert "restaurant" in prompt
    assert "Brooklyn" in prompt


def test_retries_on_invalid_json():
    client = MagicMock()
    bad = MagicMock()
    bad.content = [MagicMock(text="not json")]
    good = MagicMock()
    good.content = [MagicMock(text=json.dumps({"outcome": "accepted", "opt_out": False, "call_brief": {}}))]
    client.messages.create = MagicMock(side_effect=[bad, good])
    result = analyze_transcript("user: yes", SAMPLE_LEAD, client)
    assert result["outcome"] == "accepted"
    assert client.messages.create.call_count == 2


def test_raises_after_3_retries_with_invalid_json():
    client = MagicMock()
    bad = MagicMock()
    bad.content = [MagicMock(text="not json")]
    client.messages.create = MagicMock(return_value=bad)
    with pytest.raises(AnalysisError):
        analyze_transcript("foo", SAMPLE_LEAD, client)
    assert client.messages.create.call_count == 3


def test_raises_on_missing_outcome_key():
    client = make_claude_returning({"opt_out": False, "call_brief": {}})
    with pytest.raises(AnalysisError):
        analyze_transcript("foo", SAMPLE_LEAD, client)
