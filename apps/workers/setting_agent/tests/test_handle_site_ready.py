"""Tests for D-Phase2 _handle_site_ready handler."""
import os
from unittest.mock import patch, MagicMock
import pytest

from apps.workers.setting_agent.main import SettingAgent, MAX_SALES_CALL_ATTEMPTS


def _make_agent(client=None):
    if client is None:
        client = MagicMock()
    with patch.dict(os.environ, {
        "ANTHROPIC_API_KEY": "test",
        "ELEVENLABS_API_KEY": "test",
        "ELEVENLABS_AGENT_ID": "agent_cold",
        "ELEVENLABS_AGENT_PHONE_NUMBER_ID": "phn_xxx",
        "ELEVENLABS_SALES_AGENT_ID": "agent_sales",
    }):
        agent = SettingAgent(supabase_client=client)
    return agent, client


def _mock_supabase_for_site_ready(site_attempts=0):
    client = MagicMock()
    site = {
        "id": "site-1",
        "lead_id": "lead-1",
        "slug": "mario-pizza",
        "sales_call_attempts": site_attempts,
    }
    lead = {"id": "lead-1", "company_name": "Mario", "phone": "+393477544532", "email": "mario@example.com"}

    sel_site_eq = MagicMock()
    sel_site_eq.limit = MagicMock(return_value=sel_site_eq)
    sel_site_eq.execute = MagicMock(return_value=MagicMock(data=[site]))

    sel_lead_eq = MagicMock()
    sel_lead_eq.limit = MagicMock(return_value=sel_lead_eq)
    sel_lead_eq.execute = MagicMock(return_value=MagicMock(data=[lead]))

    sel_dnc_eq = MagicMock()
    sel_dnc_eq.limit = MagicMock(return_value=sel_dnc_eq)
    sel_dnc_eq.execute = MagicMock(return_value=MagicMock(data=[]))

    def select_router(name):
        t = MagicMock()
        sel = MagicMock()
        sel_eq_router = {
            "sites": sel_site_eq,
            "leads": sel_lead_eq,
            "do_not_call": sel_dnc_eq,
        }
        sel.eq = MagicMock(return_value=sel_eq_router.get(name, MagicMock()))
        t.select = MagicMock(return_value=sel)

        upd = MagicMock()
        upd.eq = MagicMock(return_value=upd)
        upd.execute = MagicMock(return_value=MagicMock())
        t.update = MagicMock(return_value=upd)
        t.insert = MagicMock(return_value=MagicMock(execute=MagicMock(return_value=MagicMock())))
        t.delete = MagicMock(return_value=MagicMock(eq=MagicMock(return_value=MagicMock(execute=MagicMock()))))
        return t

    client.table.side_effect = select_router
    return client


@pytest.mark.asyncio
async def test_handle_site_ready_triggers_sales_call_when_attempts_zero():
    client = _mock_supabase_for_site_ready(site_attempts=0)
    agent, _ = _make_agent(client)
    agent._elevenlabs = MagicMock()
    agent._elevenlabs.trigger_outbound_call.return_value = {
        "conversation_id": "conv_xxx",
        "callSid": "CA_xxx",
    }

    event = {
        "type": "builder.site_ready",
        "payload": {"site_id": "site-1", "lead_id": "lead-1"},
    }
    new_events = await agent._handle_site_ready(event)

    agent._elevenlabs.trigger_outbound_call.assert_called_once()
    call_kwargs = agent._elevenlabs.trigger_outbound_call.call_args.kwargs
    assert call_kwargs["agent_id"] == "agent_sales"
    assert call_kwargs["to_number"] == "+393477544532"

    assert len(new_events) == 1
    assert new_events[0]["type"] == "setting.sales_call_initiated"
    assert new_events[0]["payload"]["site_id"] == "site-1"


@pytest.mark.asyncio
async def test_handle_site_ready_skips_when_max_attempts():
    client = _mock_supabase_for_site_ready(site_attempts=MAX_SALES_CALL_ATTEMPTS)
    agent, _ = _make_agent(client)
    agent._elevenlabs = MagicMock()

    event = {"type": "builder.site_ready", "payload": {"site_id": "site-1", "lead_id": "lead-1"}}
    result = await agent._handle_site_ready(event)
    assert result == []
    agent._elevenlabs.trigger_outbound_call.assert_not_called()


@pytest.mark.asyncio
async def test_handle_site_ready_no_phone_returns_empty():
    client = MagicMock()
    site = {"id": "site-1", "lead_id": "lead-1", "slug": "x", "sales_call_attempts": 0}
    lead_no_phone = {"id": "lead-1", "company_name": "X", "phone": None, "email": "x@x.com"}

    def select_router(name):
        t = MagicMock()
        sel_eq = MagicMock()
        sel_eq.limit = MagicMock(return_value=sel_eq)
        if name == "sites":
            sel_eq.execute = MagicMock(return_value=MagicMock(data=[site]))
        elif name == "leads":
            sel_eq.execute = MagicMock(return_value=MagicMock(data=[lead_no_phone]))
        else:
            sel_eq.execute = MagicMock(return_value=MagicMock(data=[]))
        sel = MagicMock()
        sel.eq = MagicMock(return_value=sel_eq)
        t.select = MagicMock(return_value=sel)
        return t

    client.table.side_effect = select_router

    agent, _ = _make_agent(client)
    agent._elevenlabs = MagicMock()
    event = {"type": "builder.site_ready", "payload": {"site_id": "site-1", "lead_id": "lead-1"}}
    result = await agent._handle_site_ready(event)
    assert result == []
    agent._elevenlabs.trigger_outbound_call.assert_not_called()
