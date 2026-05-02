"""Tests for D-Phase2 _handle_sales_call_completed handler."""
import os
from unittest.mock import patch, MagicMock
import pytest

from apps.workers.setting_agent.main import SettingAgent


def _make_agent(client=None):
    if client is None:
        client = MagicMock()
    with patch.dict(os.environ, {
        "ANTHROPIC_API_KEY": "test",
        "ELEVENLABS_API_KEY": "test",
        "ELEVENLABS_AGENT_ID": "agent_cold",
        "ELEVENLABS_AGENT_PHONE_NUMBER_ID": "phn_xxx",
        "ELEVENLABS_SALES_AGENT_ID": "agent_sales",
        "STRIPE_SECRET_KEY": "sk_test",
        "STRIPE_PRICE_ID": "price_xxx",
        "CUSTOMER_DASHBOARD_URL": "https://customer-dashboard-ashen.vercel.app",
        "TWILIO_ACCOUNT_SID": "AC",
        "TWILIO_AUTH_TOKEN": "tok",
        "TWILIO_PHONE_NUMBER": "+1xxx",
    }):
        agent = SettingAgent(supabase_client=client)
    return agent, client


def _mock_supabase_for_completed(site_data=None, lead_data=None):
    client = MagicMock()
    site = site_data or {
        "id": "site-1",
        "lead_id": "lead-1",
        "slug": "mario-pizza",
    }
    lead = lead_data or {
        "id": "lead-1",
        "company_name": "Mario",
        "phone": "+393477544532",
        "email": "mario@example.com",
    }

    sel_site_eq = MagicMock()
    sel_site_eq.limit = MagicMock(return_value=sel_site_eq)
    sel_site_eq.execute = MagicMock(return_value=MagicMock(data=[site]))

    sel_lead_eq = MagicMock()
    sel_lead_eq.limit = MagicMock(return_value=sel_lead_eq)
    sel_lead_eq.execute = MagicMock(return_value=MagicMock(data=[lead]))

    def select_router(name):
        t = MagicMock()
        sel = MagicMock()
        if name == "sites":
            sel.eq = MagicMock(return_value=sel_site_eq)
        elif name == "leads":
            sel.eq = MagicMock(return_value=sel_lead_eq)
        else:
            sel_eq = MagicMock()
            sel_eq.limit = MagicMock(return_value=sel_eq)
            sel_eq.execute = MagicMock(return_value=MagicMock(data=[]))
            sel.eq = MagicMock(return_value=sel_eq)
        t.select = MagicMock(return_value=sel)

        upd = MagicMock()
        upd.eq = MagicMock(return_value=upd)
        upd.execute = MagicMock(return_value=MagicMock())
        t.update = MagicMock(return_value=upd)

        ins = MagicMock()
        ins.execute = MagicMock(return_value=MagicMock())
        t.insert = MagicMock(return_value=ins)

        delete = MagicMock()
        delete_eq = MagicMock()
        delete_eq.execute = MagicMock(return_value=MagicMock())
        delete.eq = MagicMock(return_value=delete_eq)
        t.delete = MagicMock(return_value=delete)
        return t

    client.table.side_effect = select_router
    return client


@pytest.mark.asyncio
@patch("apps.workers.setting_agent.main.send_sms")
@patch("apps.workers.setting_agent.main.create_stripe_checkout")
@patch("apps.workers.setting_agent.main.analyze_sales_transcript")
async def test_accepted_pay_creates_checkout_and_sends_sms(mock_analyze, mock_checkout, mock_sms):
    mock_analyze.return_value = {"outcome": "accepted_pay", "sales_brief": "yes"}
    mock_checkout.return_value = ("https://checkout.stripe.com/c/pay/cs_xxx", "cs_xxx")
    mock_sms.return_value = "SM_123"

    client = _mock_supabase_for_completed()
    agent, _ = _make_agent(client)

    event = {
        "type": "setting.sales_call_completed",
        "payload": {"site_id": "site-1", "transcript": "Yes I'll pay"},
    }
    new_events = await agent._handle_sales_call_completed(event)

    mock_checkout.assert_called_once()
    mock_sms.assert_called_once()
    sms_kwargs = mock_sms.call_args.kwargs
    assert sms_kwargs["to"] == "+393477544532"
    assert "https://checkout.stripe.com" in sms_kwargs["body"]

    assert len(new_events) == 1
    assert new_events[0]["type"] == "setting.payment_link_sent"
    assert new_events[0]["payload"]["channel"] == "sms"


@pytest.mark.asyncio
@patch("apps.workers.setting_agent.main.send_sms")
@patch("apps.workers.setting_agent.main.create_stripe_checkout")
@patch("apps.workers.setting_agent.main.analyze_sales_transcript")
async def test_interested_no_call_also_sends_sms(mock_analyze, mock_checkout, mock_sms):
    mock_analyze.return_value = {"outcome": "interested_no_call", "sales_brief": "thinking"}
    mock_checkout.return_value = ("https://checkout.stripe.com/c/pay/cs_xxx", "cs_xxx")
    mock_sms.return_value = "SM_123"

    client = _mock_supabase_for_completed()
    agent, _ = _make_agent(client)

    event = {"type": "setting.sales_call_completed", "payload": {"site_id": "site-1", "transcript": "thinking"}}
    new_events = await agent._handle_sales_call_completed(event)

    mock_sms.assert_called_once()
    assert new_events[0]["type"] == "setting.payment_link_sent"


@pytest.mark.asyncio
@patch("apps.workers.setting_agent.main.send_sms")
@patch("apps.workers.setting_agent.main.create_stripe_checkout")
@patch("apps.workers.setting_agent.main.analyze_sales_transcript")
async def test_rejected_deletes_site_and_adds_to_dnc(mock_analyze, mock_checkout, mock_sms):
    mock_analyze.return_value = {"outcome": "rejected", "sales_brief": "no"}
    client = _mock_supabase_for_completed()
    agent, _ = _make_agent(client)

    event = {"type": "setting.sales_call_completed", "payload": {"site_id": "site-1", "transcript": "no"}}
    new_events = await agent._handle_sales_call_completed(event)

    mock_checkout.assert_not_called()
    mock_sms.assert_not_called()

    assert len(new_events) == 1
    assert new_events[0]["type"] == "site.deleted_unpaid"
    assert new_events[0]["payload"]["reason"] == "rejected"


@pytest.mark.asyncio
@patch("apps.workers.setting_agent.main.send_sms")
@patch("apps.workers.setting_agent.main.create_stripe_checkout")
@patch("apps.workers.setting_agent.main.analyze_sales_transcript")
async def test_unclear_returns_empty(mock_analyze, mock_checkout, mock_sms):
    mock_analyze.return_value = {"outcome": "unclear", "sales_brief": "ambiguous"}
    client = _mock_supabase_for_completed()
    agent, _ = _make_agent(client)

    event = {"type": "setting.sales_call_completed", "payload": {"site_id": "site-1", "transcript": "..."}}
    result = await agent._handle_sales_call_completed(event)

    mock_checkout.assert_not_called()
    mock_sms.assert_not_called()
    assert result == []
