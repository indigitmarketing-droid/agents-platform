import os
import json
import pytest
from unittest.mock import MagicMock, patch
from apps.workers.setting_agent.main import SettingAgent


SAMPLE_LEAD = {
    "id": "lead-1",
    "name": "Joe's Pizza",
    "phone": "+15551234567",
    "email": "joe@example.com",
    "category": "restaurant",
    "city": "Brooklyn",
    "country_code": "US",
}


def make_supabase_with_call_log_and_lead():
    """Mock supabase that returns proper data for call_logs lookup + lead lookup."""
    client = MagicMock()
    inserts = []
    updates = []

    def table_factory(name):
        t = MagicMock()
        ins = MagicMock()
        ins.execute = MagicMock(return_value=MagicMock(data=[{"id": f"{name}-uuid"}]))

        def capture_insert(row):
            inserts.append((name, row))
            return ins
        t.insert.side_effect = capture_insert

        upd = MagicMock()
        upd.eq.return_value = upd
        def capture_update(payload):
            updates.append((name, payload))
            return upd
        t.update.side_effect = capture_update

        sel = MagicMock()
        sel_eq = MagicMock()
        sel_eq.limit = MagicMock(return_value=sel_eq)
        if name == "call_logs":
            sel_eq.execute = MagicMock(return_value=MagicMock(data=[{
                "id": "log-uuid", "lead_id": "lead-1", "phone": "+15551234567"
            }]))
        elif name == "leads":
            sel_eq.execute = MagicMock(return_value=MagicMock(data=[SAMPLE_LEAD]))
        else:
            sel_eq.execute = MagicMock(return_value=MagicMock(data=[]))
        sel.eq.return_value = sel_eq
        t.select.return_value = sel
        return t

    client.table.side_effect = table_factory
    client.inserts = inserts
    client.updates = updates
    return client


def make_claude_accepted():
    client = MagicMock()
    response = MagicMock()
    response.content = [MagicMock(text=json.dumps({
        "outcome": "accepted",
        "opt_out": False,
        "call_brief": {"services": ["pizza"], "style_preference": "modern"},
    }))]
    client.messages.create = MagicMock(return_value=response)
    return client


@pytest.fixture
def env_vars():
    with patch.dict(os.environ, {
        "ANTHROPIC_API_KEY": "test-anthropic",
        "ELEVENLABS_API_KEY": "test-elevenlabs",
        "ELEVENLABS_AGENT_ID": "agent_test",
        "ELEVENLABS_AGENT_PHONE_NUMBER_ID": "phn_test",
    }):
        yield


@pytest.mark.asyncio
async def test_handles_call_completed_event_accepted(env_vars):
    supabase = make_supabase_with_call_log_and_lead()
    claude = make_claude_accepted()
    agent = SettingAgent(supabase_client=supabase)
    agent._claude = claude

    event = {
        "id": "evt-1",
        "type": "setting.call_completed",
        "payload": {
            "lead_id": "lead-1",
            "conversation_id": "conv_xxx",
            "transcript": "Agent: Hello... User: Yes I'd like a free website",
            "duration_seconds": 180,
        },
        "retry_count": 0,
    }
    new_events = await agent.handle_event(event)
    types = [e["type"] for e in new_events]
    assert "setting.call_accepted" in types

    accepted = next(e for e in new_events if e["type"] == "setting.call_accepted")
    assert accepted["target_agent"] == "builder"
    assert "call_brief" in accepted["payload"]


@pytest.mark.asyncio
async def test_ignores_unknown_event_types(env_vars):
    supabase = make_supabase_with_call_log_and_lead()
    agent = SettingAgent(supabase_client=supabase)
    event = {"id": "evt-1", "type": "scraping.lead_found", "payload": {}, "retry_count": 0}
    result = await agent.handle_event(event)
    assert result == []


@pytest.mark.asyncio
async def test_logs_website_ready_but_does_not_act(env_vars):
    """builder.website_ready is phase 2 — for now just log and return []."""
    supabase = make_supabase_with_call_log_and_lead()
    agent = SettingAgent(supabase_client=supabase)
    event = {
        "id": "evt-1",
        "type": "builder.website_ready",
        "payload": {"lead_id": "lead-1", "site_url": "https://x"},
        "retry_count": 0,
    }
    result = await agent.handle_event(event)
    assert result == []
