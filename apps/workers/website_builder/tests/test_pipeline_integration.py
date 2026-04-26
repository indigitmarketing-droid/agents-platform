"""End-to-end test of the BuilderAgent pipeline with mocked Claude + Supabase."""
import json
import os
import pytest
from unittest.mock import MagicMock, patch
from apps.workers.website_builder.main import BuilderAgent


def make_full_mock_supabase():
    client = MagicMock()
    insert_results = []

    def table_factory(name):
        t = MagicMock()
        ins = MagicMock()
        ins.execute = MagicMock(return_value=MagicMock(data=[{"id": f"{name}-uuid"}]))

        def insert_capture(row):
            insert_results.append((name, row))
            return ins
        t.insert.side_effect = insert_capture

        sel = MagicMock()
        sel.eq.return_value = sel
        sel.execute = MagicMock(return_value=MagicMock(data=[]))
        t.select.return_value = sel

        upd = MagicMock()
        upd.eq.return_value = upd
        upd.execute = MagicMock()
        t.update.return_value = upd

        return t

    client.table.side_effect = table_factory
    client.insert_results = insert_results
    return client


def make_full_mock_claude():
    client = MagicMock()
    palette = MagicMock()
    palette.content = [MagicMock(text=json.dumps({
        "primary": "#8B4513", "accent": "#D4A574",
        "text": "#2C2C2C", "background": "#FAF7F2",
    }))]
    content = MagicMock()
    content.content = [MagicMock(text=json.dumps({
        "hero": {"headline": "Bella Pizza", "subheadline": "Tradizione", "cta_text": "Prenota", "cta_link": "#contact", "image_url": "https://images.unsplash.com/photo-1"},
        "problem": {"title": "Il problema", "body": "B", "bullets": ["x"]},
        "benefits": {"title": "Vantaggi", "items": [{"title": "a", "description": "b"}]},
        "solution": {"title": "Come", "body": "B", "cta_text": "Vai", "cta_link": "#contact"},
        "services": [{"title": "Pizza al taglio", "description": "Veloce e buona"}],
        "contacts": {"phone": "+39028373248", "email": None, "address": "Via Roma", "opening_hours": "12-23"},
    }))]
    client.messages.create = MagicMock(side_effect=[palette, content])
    return client


@pytest.mark.asyncio
async def test_full_pipeline_creates_site_and_emits_event():
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test"}):
        supabase = make_full_mock_supabase()
        claude = make_full_mock_claude()
        agent = BuilderAgent(supabase_client=supabase)
        agent._claude = claude

        event = {
            "id": "evt-1",
            "type": "setting.call_accepted",
            "payload": {
                "lead_id": "lead-1",
                "lead": {
                    "name": "Pizzeria Da Mario",
                    "phone": "+39028373248",
                    "category": "restaurant",
                    "city": "Milano",
                },
                "call_brief": {
                    "custom_requests": "Enfatizza la pizza al taglio",
                    "style_preference": "tradizionale",
                },
            },
            "retry_count": 0,
        }
        new_events = await agent.handle_event(event)

        types = [e["type"] for e in new_events]
        assert "builder.build_started" in types
        assert "builder.website_ready" in types

        sites_inserts = [r for name, r in supabase.insert_results if name == "sites"]
        assert len(sites_inserts) == 1
        site = sites_inserts[0]
        assert site["lead_id"] == "lead-1"
        assert site["template_kind"] == "hospitality"
        assert site["category"] == "restaurant"
        assert site["colors"]["primary"] == "#8B4513"
        assert site["content"]["hero"]["headline"] == "Bella Pizza"
        assert site["slug"] == "pizzeria-da-mario"
        assert site["published_url"].endswith("/s/pizzeria-da-mario")

        assert claude.messages.create.call_count == 2


@pytest.mark.asyncio
async def test_pipeline_works_without_call_brief():
    """Graceful degradation: no call_brief → still produces a site."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test"}):
        supabase = make_full_mock_supabase()
        claude = make_full_mock_claude()
        agent = BuilderAgent(supabase_client=supabase)
        agent._claude = claude

        event = {
            "id": "evt-1",
            "type": "setting.call_accepted",
            "payload": {
                "lead_id": "lead-1",
                "lead": {"name": "Test", "phone": "+39021", "category": "restaurant", "city": "Milano"},
            },
            "retry_count": 0,
        }
        new_events = await agent.handle_event(event)
        types = [e["type"] for e in new_events]
        assert "builder.website_ready" in types
