import os
import json
import pytest
from unittest.mock import MagicMock, patch
from apps.workers.website_builder.main import BuilderAgent


SAMPLE_LEAD = {
    "name": "Pizzeria Da Mario",
    "phone": "+39028373248",
    "email": "info@pizzeriamario.it",
    "category": "restaurant",
    "city": "Milano",
}

SAMPLE_CONTENT = {
    "hero": {"headline": "Pizza", "subheadline": "Buona", "cta_text": "Vieni", "image_url": "https://images.unsplash.com/x"},
    "services": [{"title": "Pizza", "description": "Buona"}],
    "about": {"title": "About", "body": "Storia"},
    "contacts": {"phone": "+39028373248"},
}


def make_supabase_client():
    """Mock Supabase client with table()/insert/select chains."""
    client = MagicMock()

    insert_chain = MagicMock()
    insert_chain.execute = MagicMock(return_value=MagicMock(data=[{"id": "site-uuid"}]))

    update_chain = MagicMock()
    update_chain.eq.return_value = update_chain
    update_chain.execute = MagicMock()

    # select for slug check returns empty (no collisions)
    select_chain = MagicMock()
    select_chain.eq.return_value = select_chain
    select_chain.execute = MagicMock(return_value=MagicMock(data=[]))

    def table_factory(_name):
        t = MagicMock()
        t.insert.return_value = insert_chain
        t.update.return_value = update_chain
        t.select.return_value = select_chain
        return t

    client.table.side_effect = table_factory
    return client


def make_claude_client():
    """Mock Claude returning valid palette + content sequentially."""
    client = MagicMock()
    palette_response = MagicMock()
    palette_response.content = [MagicMock(text=json.dumps({
        "primary": "#8B4513", "accent": "#D4A574", "text": "#2C2C2C", "background": "#FAF7F2",
    }))]
    content_response = MagicMock()
    content_response.content = [MagicMock(text=json.dumps(SAMPLE_CONTENT))]
    client.messages.create = MagicMock(side_effect=[palette_response, content_response])
    return client


@pytest.fixture
def env_vars():
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        yield


@pytest.mark.asyncio
async def test_handles_call_accepted_event(env_vars):
    supabase = make_supabase_client()
    claude = make_claude_client()
    agent = BuilderAgent(supabase_client=supabase)
    agent._claude = claude

    event = {
        "id": "evt-1",
        "type": "setting.call_accepted",
        "payload": {"lead_id": "lead-1", "lead": SAMPLE_LEAD},
        "retry_count": 0,
    }
    new_events = await agent.handle_event(event)
    types = [e["type"] for e in new_events]
    assert "builder.build_started" in types
    assert "builder.website_ready" in types


@pytest.mark.asyncio
async def test_website_ready_targets_setting(env_vars):
    supabase = make_supabase_client()
    claude = make_claude_client()
    agent = BuilderAgent(supabase_client=supabase)
    agent._claude = claude

    event = {
        "id": "evt-1",
        "type": "setting.call_accepted",
        "payload": {"lead_id": "lead-1", "lead": SAMPLE_LEAD},
        "retry_count": 0,
    }
    new_events = await agent.handle_event(event)
    ready = next(e for e in new_events if e["type"] == "builder.website_ready")
    assert ready["target_agent"] == "setting"
    assert "site_url" in ready["payload"]
    assert "lead_id" in ready["payload"]
    assert ready["payload"]["lead_id"] == "lead-1"


@pytest.mark.asyncio
async def test_inserts_site_in_db(env_vars):
    supabase = make_supabase_client()
    claude = make_claude_client()
    agent = BuilderAgent(supabase_client=supabase)
    agent._claude = claude

    event = {
        "id": "evt-1",
        "type": "setting.call_accepted",
        "payload": {"lead_id": "lead-1", "lead": SAMPLE_LEAD},
        "retry_count": 0,
    }
    await agent.handle_event(event)

    inserts_to_sites = [
        call for call in supabase.table.call_args_list
        if call.args[0] == "sites"
    ]
    assert len(inserts_to_sites) > 0


@pytest.mark.asyncio
async def test_uses_base_url_env_var(env_vars):
    with patch.dict(os.environ, {
        "ANTHROPIC_API_KEY": "test-key",
        "AGENTS_SITES_BASE_URL": "https://custom.example.com",
    }):
        supabase = make_supabase_client()
        claude = make_claude_client()
        agent = BuilderAgent(supabase_client=supabase)
        agent._claude = claude

        event = {
            "id": "evt-1",
            "type": "setting.call_accepted",
            "payload": {"lead_id": "lead-1", "lead": SAMPLE_LEAD},
            "retry_count": 0,
        }
        new_events = await agent.handle_event(event)
        ready = next(e for e in new_events if e["type"] == "builder.website_ready")
        assert ready["payload"]["site_url"].startswith("https://custom.example.com/s/")


@pytest.mark.asyncio
async def test_ignores_unknown_event_types(env_vars):
    supabase = make_supabase_client()
    agent = BuilderAgent(supabase_client=supabase)

    event = {
        "id": "evt-1",
        "type": "scraping.lead_found",
        "payload": {},
        "retry_count": 0,
    }
    result = await agent.handle_event(event)
    assert result == []
