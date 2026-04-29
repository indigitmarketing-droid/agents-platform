"""End-to-end test: webhook event → Claude analyze → setting.call_accepted emitted."""
import json
import os
import pytest
from unittest.mock import MagicMock, patch
from apps.workers.setting_agent.main import SettingAgent


SAMPLE_LEAD = {
    "id": "lead-1",
    "name": "Joe's Pizza",
    "phone": "+15551234567",
    "category": "restaurant",
    "city": "Brooklyn",
    "country_code": "US",
    "call_attempts": 1,
}


def make_full_mock():
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
        sel_eq.maybe_single = MagicMock(return_value=sel_eq)
        if name == "call_logs":
            sel_eq.execute = MagicMock(return_value=MagicMock(data={
                "id": "log-uuid", "lead_id": "lead-1", "phone": "+15551234567"
            }))
        elif name == "leads":
            sel_eq.execute = MagicMock(return_value=MagicMock(data=SAMPLE_LEAD))
        else:
            sel_eq.execute = MagicMock(return_value=MagicMock(data=None))
        sel.eq.return_value = sel_eq
        t.select.return_value = sel
        return t

    client.table.side_effect = table_factory
    client.inserts = inserts
    client.updates = updates
    return client


def make_claude(outcome="accepted"):
    client = MagicMock()
    response = MagicMock()
    if outcome == "accepted":
        response.content = [MagicMock(text=json.dumps({
            "outcome": "accepted",
            "opt_out": False,
            "call_brief": {"services": ["pizza", "delivery"], "style_preference": "modern"},
        }))]
    elif outcome == "rejected":
        response.content = [MagicMock(text=json.dumps({
            "outcome": "rejected", "opt_out": False, "call_brief": None,
        }))]
    elif outcome == "opt_out":
        response.content = [MagicMock(text=json.dumps({
            "outcome": "rejected", "opt_out": True, "call_brief": None,
        }))]
    client.messages.create = MagicMock(return_value=response)
    return client


@pytest.mark.asyncio
async def test_pipeline_accepted_emits_call_accepted_to_builder():
    with patch.dict(os.environ, {
        "ANTHROPIC_API_KEY": "test", "ELEVENLABS_API_KEY": "test",
        "ELEVENLABS_AGENT_ID": "agent_test", "ELEVENLABS_AGENT_PHONE_NUMBER_ID": "phn_test",
    }):
        supabase = make_full_mock()
        agent = SettingAgent(supabase_client=supabase)
        agent._claude = make_claude("accepted")

        event = {
            "id": "evt-1", "type": "setting.call_completed",
            "payload": {
                "lead_id": "lead-1",
                "conversation_id": "conv_xxx",
                "transcript": "Agent: Want a free site? User: Yes!",
                "duration_seconds": 240,
            },
            "retry_count": 0,
        }
        new_events = await agent.handle_event(event)
        assert len(new_events) == 1
        assert new_events[0]["type"] == "setting.call_accepted"
        assert new_events[0]["target_agent"] == "builder"
        assert new_events[0]["payload"]["call_brief"]["services"] == ["pizza", "delivery"]


@pytest.mark.asyncio
async def test_pipeline_rejected_emits_call_rejected():
    with patch.dict(os.environ, {
        "ANTHROPIC_API_KEY": "test", "ELEVENLABS_API_KEY": "test",
        "ELEVENLABS_AGENT_ID": "agent_test", "ELEVENLABS_AGENT_PHONE_NUMBER_ID": "phn_test",
    }):
        supabase = make_full_mock()
        agent = SettingAgent(supabase_client=supabase)
        agent._claude = make_claude("rejected")

        event = {
            "id": "evt-1", "type": "setting.call_completed",
            "payload": {
                "lead_id": "lead-1",
                "conversation_id": "conv_xxx",
                "transcript": "User: No thanks",
                "duration_seconds": 30,
            },
            "retry_count": 0,
        }
        new_events = await agent.handle_event(event)
        assert len(new_events) == 1
        assert new_events[0]["type"] == "setting.call_rejected"


@pytest.mark.asyncio
async def test_pipeline_opt_out_adds_to_dnc():
    with patch.dict(os.environ, {
        "ANTHROPIC_API_KEY": "test", "ELEVENLABS_API_KEY": "test",
        "ELEVENLABS_AGENT_ID": "agent_test", "ELEVENLABS_AGENT_PHONE_NUMBER_ID": "phn_test",
    }):
        supabase = make_full_mock()
        agent = SettingAgent(supabase_client=supabase)
        agent._claude = make_claude("opt_out")

        event = {
            "id": "evt-1", "type": "setting.call_completed",
            "payload": {
                "lead_id": "lead-1",
                "conversation_id": "conv_xxx",
                "transcript": "User: Don't call again!",
                "duration_seconds": 15,
            },
            "retry_count": 0,
        }
        await agent.handle_event(event)

        dnc_inserts = [r for name, r in supabase.inserts if name == "do_not_call"]
        assert len(dnc_inserts) == 1
        assert dnc_inserts[0]["phone"] == "+15551234567"
        assert dnc_inserts[0]["reason"] == "lead_request"
