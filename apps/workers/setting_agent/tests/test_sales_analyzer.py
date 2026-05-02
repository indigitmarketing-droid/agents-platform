"""Tests for sales transcript analyzer."""
import json
from unittest.mock import MagicMock
import pytest

from apps.workers.setting_agent.sales_analyzer import analyze_sales_transcript
from apps.workers.setting_agent.transcript_analyzer import AnalysisError


def _mock_claude(outcomes_sequence):
    """Mock claude_client.messages.create to return outcomes in sequence (allows retry tests)."""
    client = MagicMock()
    responses = []
    for outcome in outcomes_sequence:
        if outcome.startswith("MALFORMED:"):
            r = MagicMock()
            r.content = [MagicMock(text=outcome[len("MALFORMED:"):])]
            responses.append(r)
        else:
            r = MagicMock()
            r.content = [MagicMock(text=json.dumps({
                "outcome": outcome,
                "sales_brief": f"Customer outcome: {outcome}",
            }))]
            responses.append(r)
    client.messages.create.side_effect = responses
    return client


def _sample_lead():
    return {"id": "lead-1", "company_name": "Mario Pizza", "phone": "+393477544532"}


def test_analyze_returns_accepted_pay():
    claude = _mock_claude(["accepted_pay"])
    result = analyze_sales_transcript("Customer: Yes I'll pay", _sample_lead(), claude)
    assert result["outcome"] == "accepted_pay"
    assert "sales_brief" in result


def test_analyze_returns_rejected():
    claude = _mock_claude(["rejected"])
    result = analyze_sales_transcript("Customer: Not interested", _sample_lead(), claude)
    assert result["outcome"] == "rejected"


def test_analyze_returns_interested_no_call():
    claude = _mock_claude(["interested_no_call"])
    result = analyze_sales_transcript("Customer: Send me an email", _sample_lead(), claude)
    assert result["outcome"] == "interested_no_call"


def test_analyze_empty_transcript_raises():
    claude = MagicMock()
    with pytest.raises(AnalysisError, match="empty transcript"):
        analyze_sales_transcript("", _sample_lead(), claude)


def test_analyze_retries_on_malformed_then_succeeds():
    claude = _mock_claude(["MALFORMED:not json", "MALFORMED:still bad", "accepted_pay"])
    result = analyze_sales_transcript("Customer: yes", _sample_lead(), claude)
    assert result["outcome"] == "accepted_pay"
    assert claude.messages.create.call_count == 3


def test_analyze_raises_after_max_retries():
    claude = _mock_claude(["MALFORMED:bad"] * 4)
    with pytest.raises(AnalysisError, match="Could not parse"):
        analyze_sales_transcript("Customer: yes", _sample_lead(), claude)
